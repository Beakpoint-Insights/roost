#!/usr/bin/env python3
"""Reads a run's Claude Code transcripts for the retro skill and prints one JSON object.

  moments TRANSCRIPT... [--since ISO] [--until ISO] [--config FILE]... [--repo-of PATH=REPO]...
      The moments worth a finding (corrections, refusals, errors, retries, long searches,
      slow steps, stops for the user, blocks), with totals per session.

Exit 0 whatever it finds (unreadable records are in the JSON), 2 for bad arguments,
1 for a failure of its own, with {"error": "<type>: <message>"}.

Standard library only. Run it from the skill's own folder: <skill folder>/scripts/.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

EXCERPT = 300            # characters kept in an excerpt
SLOW_SECONDS = 120       # a tool call at least this long is slow
TURN_MINUTES = 30        # a turn at least this long is slow (kind "turn")
SEARCH_MIN = 10          # reads and searches in a row before the first edit
RETRY_WINDOW = 5         # tool calls back to look for the same call
KNOWN_TYPES = {"user", "assistant", "system", "attachment", "summary", "api-request", "api-request-blob",
               "api-request-shape", "last-prompt", "mode", "permission-mode", "atis-latch", "pr-link",
               "queue-operation", "ai-title", "custom-title", "agent-name", "file-history-snapshot",
               "file-history-delta", "frame-link", "tools-used", "artifact-autoreact-ledger", "cost-state",
               "artifact-comment-monitor"}
SEARCH_TOOLS = {"Read", "Grep", "Glob", "LS"}
READ_ONLY_BASH = re.compile(r"^(?:cd \S+ && )?(?:grep|rg|find|ls|cat|head|tail|sed -n|wc|git (?:log|show|grep|diff|status))\b")
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
USER_WAIT_TOOLS = {"AskUserQuestion"}
NOT_TYPED = ("<command-", "<local-command-", "<bash-", "<system-reminder>", "<task-notification",
             "<cross-session-message", "[Cross-session ")
SIGNING = [re.compile(p, re.I) for p in (r"gpg failed to sign", r"failed to sign the data", r"error: signing failed")]
SIGN_IN = [re.compile(p, re.I) for p in (r"gh auth login", r"not logged in", r"HTTP 401", r"authentication required")]
HOOK_BLOCK = re.compile(r"\bhook\b.*\b(?:block|blocked|denied|deny)\b|\b(?:block|blocked|denied)\b.*\bhook\b", re.I | re.S)
DELIVERY = re.compile(r"^\[Cross-session delivery notice\]", re.M)


def parse_time(value):
    if not value:
        return None
    return datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))


def minutes_between(a, b):
    return round((parse_time(b) - parse_time(a)).total_seconds() / 60, 1)


def records(path):
    """Yields (line number, record, None) for each JSON line, and (line number, None, reason) for each it can't read."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            last = n == len(lines) and not line.endswith("\n")
            yield n, None, "incomplete last line (still being written?)" if last else "not JSON"
            continue
        if not isinstance(rec, dict):
            yield n, None, "not a JSON object"
            continue
        if rec.get("type") in ("user", "assistant") and not isinstance(rec.get("message"), dict):
            yield n, None, "missing message"
            continue
        yield n, rec, None


def blocks(rec):
    content = (rec.get("message") or {}).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def block_text(block):
    if block.get("type") == "text":
        return block.get("text") or ""
    content = block.get("content")
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


def plain_text(rec):
    return "\n".join(block_text(b) for b in blocks(rec) if b.get("type") == "text")


def human_text(rec):
    """The user's own typed message, or None: origin.kind == "human", or no origin with promptSource "typed";
    never isMeta, a tool result, a peer message, a task notification, or a <command-name>/<local-command-*>/
    <bash-input>/<bash-stdout> wrapper. "[Request interrupted by user" counts (the user stopped the agent)."""
    if rec.get("type") != "user" or rec.get("isMeta"):
        return None
    origin = rec.get("origin")
    if origin:
        if origin.get("kind") != "human":
            return None
    elif rec.get("promptSource") != "typed":
        return None
    if any(b.get("type") == "tool_result" for b in blocks(rec)):
        return None
    text = plain_text(rec).strip()
    if not text or text.startswith(NOT_TYPED):
        return None
    return text


def trim(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= EXCERPT else text[:EXCERPT - 1] + "…"


def summary(name, inp):
    """What a tool call did, in a few words: its command, file or pattern."""
    inp = inp if isinstance(inp, dict) else {}
    for key in ("command", "file_path", "pattern", "path", "url", "query"):
        if inp.get(key):
            return str(inp[key])
    if name == "AskUserQuestion":
        return " / ".join(q.get("question", "") for q in inp.get("questions", []) if isinstance(q, dict))
    return json.dumps(inp, sort_keys=True)


def first_lines(text, n=3):
    return "\n".join((text or "").strip().splitlines()[:n])


def matches_any(patterns, text):
    return any(p.search(text) for p in patterns)


def repo_of(cwd, repo_map):
    for prefix, repo in repo_map:
        if cwd and (cwd == prefix or cwd.startswith(prefix.rstrip("/") + "/")):
            return repo
    return os.path.basename((cwd or "").rstrip("/")) or None


class Session:
    """One transcript read into what the moments need."""

    def __init__(self, path, opts):
        self.path = path
        self.opts = opts
        self.id = None
        self.title = None
        self.cwd = None
        self.events = []        # (time, moment) found in this transcript, before the window
        self.calls = []         # tool calls in order: dicts with name, input, id, time, result info
        self.unparseable = []
        self.unknown_types = {}
        self.unknown_shapes = {"hook": [], "delivery": []}

    @property
    def name(self):
        return self.title or (self.id or os.path.basename(self.path))[:8]

    def moment(self, kind, rec, **fields):
        return dict({"kind": kind, "session": None, "time": rec.get("timestamp"), "id": rec.get("uuid")}, **fields)

    def read(self):
        pending = {}
        seen_human = False
        last_assistant = None
        for n, rec, reason in records(self.path):
            if rec is None:
                self.unparseable.append({"session": None, "line": n, "reason": reason})
                continue
            kind = rec.get("type")
            if kind not in KNOWN_TYPES:
                self.unknown_types[kind] = self.unknown_types.get(kind, 0) + 1
                continue
            if kind == "custom-title" and rec.get("customTitle"):
                self.title = rec["customTitle"]
            elif kind == "agent-name" and rec.get("agentName") and not self.title:
                self.title = rec["agentName"]
            self.id = self.id or rec.get("sessionId")
            self.cwd = self.cwd or rec.get("cwd")
            if kind == "system" and rec.get("subtype") == "stop_hook_summary" and rec.get("preventedContinuation"):
                self.unknown_shapes["hook"].append({"session": None, "line": n, "id": rec.get("uuid")})
            if kind == "assistant":
                last_assistant = self.read_assistant(rec, pending) or last_assistant
            elif kind == "user":
                text = human_text(rec)
                if DELIVERY.search(plain_text(rec)):
                    self.unknown_shapes["delivery"].append({"session": None, "line": n, "id": rec.get("uuid")})
                if text is not None:
                    if last_assistant is not None and plain_text(last_assistant).rstrip().endswith("?"):
                        self.events.append(self.moment("stop", last_assistant, excerpt=plain_text(last_assistant),
                                                       waited_minutes=minutes_between(last_assistant["timestamp"], rec["timestamp"])))
                    if seen_human:
                        self.events.append(self.moment("correction", rec, excerpt=text))
                    seen_human = True
                    last_assistant = None
                if rec.get("usageLimitNote"):
                    self.events.append(self.moment("blocked", rec, why="usage_limit", excerpt=plain_text(rec)))
                self.read_results(rec, n, pending)

    def read_assistant(self, rec, pending):
        if rec.get("isApiErrorMessage"):
            if rec.get("apiErrorStatus") == 429:
                self.events.append(self.moment("blocked", rec, why="usage_limit", excerpt=plain_text(rec)))
            else:
                self.events.append(self.moment("error", rec, tool=None, excerpt=plain_text(rec)))
            return None
        for b in blocks(rec):
            if b.get("type") == "tool_use":
                call = {"name": b.get("name"), "input": b.get("input") or {}, "rec": rec, "result": None}
                pending[b.get("id")] = call
                self.calls.append(call)
                if call["name"] in USER_WAIT_TOOLS:
                    call["stop"] = True
        return rec

    def read_results(self, rec, n, pending):
        for b in blocks(rec):
            if b.get("type") != "tool_result":
                continue
            call = pending.pop(b.get("tool_use_id"), None)
            text = block_text(b)
            name = call["name"] if call else None
            what = summary(name, call["input"]) if call else ""
            if call:
                call["result"] = {"rec": rec, "text": text, "error": bool(b.get("is_error"))}
                if call.get("stop"):
                    self.events.append(self.moment("stop", call["rec"], excerpt=what,
                                                   waited_minutes=minutes_between(call["rec"]["timestamp"], rec["timestamp"])))
            if rec.get("toolDenialKind"):
                self.events.append(self.moment("refusal", rec, how=rec["toolDenialKind"], tool=name, excerpt=text))
            elif matches_any(SIGNING, text) or any(s and s.lower() in text.lower() for s in self.opts.signing_errors):
                self.events.append(self.moment("blocked", rec, why="signing", excerpt=text))
            elif matches_any(SIGN_IN, text) and b.get("is_error"):
                self.events.append(self.moment("blocked", rec, why="sign_in", excerpt=text))
            elif b.get("is_error") and HOOK_BLOCK.search(text):
                self.unknown_shapes["hook"].append({"session": None, "line": n, "id": rec.get("uuid")})
            elif b.get("is_error"):
                self.events.append(self.moment("error", rec, tool=name, excerpt=(what + " → " if what else "") + first_lines(text)))

    def call_moments(self):
        """Retries, searches and slow calls, from the tool calls in order."""
        out = []
        groups = {}
        for i, call in enumerate(self.calls):
            key = (call["name"], json.dumps(call["input"], sort_keys=True))
            g = groups.get(key)
            if g and g["last"] >= i - RETRY_WINDOW:
                g["count"] += 1
                g["last"] = i
            else:
                groups[key] = g = {"first": call, "count": 1, "last": i}
                out.append(g)
        moments = [self.moment("retry", g["first"]["rec"], tool=g["first"]["name"], count=g["count"],
                               excerpt=summary(g["first"]["name"], g["first"]["input"])) for g in out if g["count"] > 1]
        run = []
        for call in self.calls + [None]:
            if call is not None and is_search(call):
                run.append(call)
                continue
            if len(run) >= SEARCH_MIN:
                end = (run[-1]["result"] or {}).get("rec") or run[-1]["rec"]
                moments.append(self.moment("search", run[0]["rec"], count=len(run),
                                           minutes=minutes_between(run[0]["rec"]["timestamp"], end["timestamp"]),
                                           excerpt=summary(run[0]["name"], run[0]["input"]) + " … "
                                           + summary(run[-1]["name"], run[-1]["input"])))
            run = []
        return moments

    def slow_runs(self):
        """Tool calls at least SLOW_SECONDS long: (group key, run)."""
        out = []
        for call in self.calls:
            if not call["result"]:
                continue
            start, end = call["rec"]["timestamp"], call["result"]["rec"]["timestamp"]
            seconds = (parse_time(end) - parse_time(start)).total_seconds()
            if seconds < SLOW_SECONDS or call["name"] in USER_WAIT_TOOLS:
                continue
            command = normalise(summary(call["name"], call["input"]))
            repo = repo_of(call["rec"].get("cwd"), self.opts.repo_map)
            out.append(((command, repo), {"session": self.name, "time": start, "id": call["rec"].get("uuid"),
                                          "minutes": round(seconds / 60, 1),
                                          "last_line": ((call["result"]["text"] or "").strip().splitlines() or [""])[-1]}))
        return out


def normalise(command):
    command = re.sub(r"^cd \S+ && ", "", command.strip())
    return re.sub(r"\s+", " ", command)


def is_search(call):
    if call["name"] in SEARCH_TOOLS:
        return True
    return call["name"] == "Bash" and bool(READ_ONLY_BASH.match(call["input"].get("command", "")))


def group_slow(runs):
    groups = {}
    for key, run in runs:
        groups.setdefault(key, []).append(run)
    out = []
    for (command, repo), group in groups.items():
        group.sort(key=lambda r: r["time"])
        last = group[-1].pop("last_line")
        for r in group[:-1]:
            r.pop("last_line")
        out.append({"kind": "slow", "kind_of": "tool", "command": command, "repo": repo, "runs": group,
                    "count": len(group), "total_minutes": round(sum(r["minutes"] for r in group), 1),
                    "excerpt": last})
    return out


def subagent_count(paths):
    found = set()
    for path in paths:
        stem = path[:-len(".jsonl")] if path.endswith(".jsonl") else path
        found.update(glob.glob(os.path.join(stem, "subagents", "*.jsonl")))
    return len(found)


def read_config_lists(paths, key):
    """Values listed under `key:` in the config files, inline ([a, b]) or as `- item` lines."""
    values = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^(\s*)" + re.escape(key) + r"\s*:\s*(.*)$", line)
            if not m:
                continue
            rest = m.group(2).split(" #")[0].strip()
            if rest.startswith("["):
                values += [unquote(v) for v in rest.strip("[]").split(",") if v.strip()]
            elif rest:
                values.append(unquote(rest))
            else:
                for item in lines[i + 1:]:
                    im = re.match(r"^\s*-\s+(.*)$", item)
                    if not im:
                        break
                    values.append(unquote(im.group(1).split(" #")[0].strip()))
    return values


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def moments(opts):
    sessions = []
    for path in opts.transcripts:
        s = Session(path, opts)
        s.read()
        sessions.append(s)
    out_moments, slow, unparseable, unknown_types = [], [], [], {}
    shapes = {"hook": [], "delivery": []}
    for s in sessions:
        for m in s.events + s.call_moments():
            m["session"] = s.name
            out_moments.append(m)
        slow += s.slow_runs()
        for u in s.unparseable:
            unparseable.append(dict(u, session=s.name))
        for k, v in s.unknown_types.items():
            unknown_types[k] = unknown_types.get(k, 0) + v
        for k in shapes:
            shapes[k] += [dict(x, session=s.name) for x in s.unknown_shapes[k]]
    slow_moments = sorted(group_slow(slow), key=lambda m: -m["total_minutes"])
    for m in out_moments + slow_moments:
        if m.get("excerpt") is not None:
            m["excerpt"] = trim(m["excerpt"])
    out_moments.sort(key=lambda m: parse_time(m["time"]))
    return {
        "window": [opts.since, opts.until],
        "sessions": [{"session": s.name, "id": s.id, "path": s.path, "repo": repo_of(s.cwd, opts.repo_map)}
                     for s in sessions],
        "moments": slow_moments + out_moments,
        "unparseable": unparseable,
        "unknown_types": unknown_types,
        "unknown_shapes": shapes,
        "subagents_not_read": subagent_count(opts.transcripts),
    }


def parse_args(argv):
    parser = argparse.ArgumentParser(prog="retro_moments.py", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    m = sub.add_parser("moments", help="moments worth a finding, with totals per session")
    m.add_argument("transcripts", nargs="+", metavar="TRANSCRIPT")
    m.add_argument("--since")
    m.add_argument("--until")
    m.add_argument("--config", action="append", default=[], metavar="FILE")
    m.add_argument("--repo-of", action="append", default=[], metavar="PATH=REPO")
    opts = parser.parse_args(argv)
    opts.repo_map = []
    for item in opts.repo_of:
        if "=" not in item:
            parser.error("--repo-of takes PATH=REPO, not %r" % item)
        path, repo = item.split("=", 1)
        opts.repo_map.append((path, repo))
    return opts


def main(argv=None):
    opts = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        opts.signing_errors = read_config_lists(opts.config, "signing_errors")
        result = moments(opts)
        code = 0
    except Exception as e:  # its own failure: say what, never a traceback
        result, code = {"error": "%s: %s" % (type(e).__name__, e)}, 1
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
