#!/usr/bin/env python3
"""Reads a run's Claude Code transcripts for the retro skill and prints one JSON object.

  moments TRANSCRIPT... [--since ISO] [--until ISO] [--config FILE]... [--repo-of PATH=REPO]...
      The moments worth a finding (corrections, refusals, errors, retries, long searches,
      slow steps, stops for the user, blocks), with totals per session; a transcript that
      can't be opened is listed in "unreadable" and the others are still read.
  redact [--config FILE]...      (text on stdin)
      The text with secrets and the team config's identifying values taken out.

Every quote it prints is redacted: generic secrets by pattern, then each identifying value in
the team config and its overrides (--config, in roost-config's order). A quote it can't clean
with confidence is dropped, and its moment kept.

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
# A read-only command: no redirect into a file (2>&1 and 2>/dev/null are fine) and no here-doc,
# outside quotes (a pattern like '=> ' is fine).
READ_ONLY_BASH = re.compile(r"""^(?!(?:[^'"]|'[^']*'|"[^"]*")*?(?:<<|(?<![2&])>(?!&)))(?:cd \S+ && )?(?:grep|rg|find|ls|cat|head|tail|sed -n|wc|git (?:log|show|grep|diff|status))\b""", re.S)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
USER_WAIT_TOOLS = {"AskUserQuestion"}
NOT_TYPED = ("<command-", "<local-command-", "<bash-", "<system-reminder>", "<task-notification",
             "<cross-session-message", "[Cross-session ")
SIGNING = [re.compile(p, re.I) for p in (r"gpg failed to sign", r"failed to sign the data", r"error: signing failed")]
SIGN_IN = [re.compile(p, re.I) for p in (r"gh auth login", r"not logged in", r"HTTP 401", r"authentication required")]
HOOK_BLOCK = re.compile(r"\bhook\b.*\b(?:block|blocked|denied|deny)\b|\b(?:block|blocked|denied)\b.*\bhook\b", re.I | re.S)
DELIVERY = re.compile(r"^\[Cross-session delivery notice\]", re.M)


SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S), "[private key]"),
    (re.compile(r"""(?i)\bauthorization["']?\s*[:=]\s*["']?[^\s"']+(?:\s+[^\s"',}]+)?["']?"""), "Authorization: [redacted]"),
    (re.compile(r"\b([a-z][a-z0-9+.-]*)://[^\s/:@]*:[^\s/@]+@\S+"), r"\1://[redacted]"),
    (re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_\w{20,}|sk-ant-[\w-]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}"
                r"|xox[abposr]-[\w-]{10,}|eyJ[\w-]+\.[\w-]+\.[\w-]+)"), "[token]"),
    # a secret's name, also inside a longer one (PGPASSWORD, GITHUB_TOKEN, client_secret) or in JSON quotes
    (re.compile(r"""(?i)\b([\w-]*?(?:password|passwd|pwd|token|secret|api[_-]?key))["']?\s*[=:]\s*(?:"(?:[^"\\]|\\.)*"|'[^']*'|[^\s"',;}]+)"""),
     r"\1=[redacted]"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[email]"),
]
UNFINISHED_KEY = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
TOKEN_LIKE = re.compile(r"[A-Za-z0-9+/=_-]{32,}")
PRIVATE_KEYS = {"site", "cloud_id", "host", "hostname", "domain", "url", "test_account_email"}
PRIVATE_SUFFIXES = ("_id", "_url", "_host", "_hostname", "_domain")
# values of private keys that name a kind of thing, not a team's own (vcs.host: github)
SYMBOLIC_VALUES = {"github", "gitlab", "bitbucket", "jira", "linear", "local", "docker", "none", "null", "true", "false"}
HOSTNAME = re.compile(r"(?<![.\w/-])[\w-]+(?:\.[\w-]+)*\.[a-z]{2,}\b", re.I)
FILE_EXTENSIONS = {"yml", "yaml", "json", "md", "py", "sh", "ts", "tsx", "js", "jsx", "txt", "html", "toml",
                   "lock", "cfg", "ini", "xml", "csv", "sql", "rb", "go", "rs", "java", "cs", "css"}
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0"}
PUBLIC_HOSTS = {"github.com", "api.github.com", "claude.ai", "anthropic.com", "figma.com", "www.figma.com"}
URL = re.compile(r"[a-z][a-z0-9+.-]*://[^\s\"'<>]+", re.I)
EMAIL_DOMAIN = re.compile(r"@([\w-]+(?:\.[\w-]+)+)")
IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)


def parse_time(value):
    """An ISO time as an aware datetime (a time with no offset is UTC), or None."""
    if not value:
        return None
    try:
        t = datetime.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=datetime.timezone.utc)


def seconds_between(a, b):
    start, end = parse_time(a), parse_time(b)
    return None if start is None or end is None else (end - start).total_seconds()


def minutes_between(a, b):
    seconds = seconds_between(a, b)
    return None if seconds is None else round(seconds / 60, 1)


EPOCH = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def time_key(value):
    """Sorts by time, with records that have none last."""
    t = parse_time(value)
    return (t is None, t or EPOCH)


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
        if rec.get("type") in ("user", "assistant"):
            if not isinstance(rec.get("message"), dict):
                yield n, None, "missing message"
                continue
            if not isinstance(rec["message"].get("content"), (str, list, type(None))):
                yield n, None, "unsupported message content"
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
    elif rec.get("promptSource") != "typed" and not plain_text(rec).startswith("[Request interrupted by user"):
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
        self.breaks = set()     # positions in calls where a human or peer message came in
        self.turns = []         # turns at least TURN_MINUTES long
        self.totals = {"turns": 0, "tool_calls": {}, "errors": 0, "minutes": 0}
        self.first = self.last = None   # first and last timestamped record in the window

    @property
    def name(self):
        """The session's title, redacted like any quote, or the start of its id."""
        fallback = (self.id or os.path.basename(self.path))[:8]
        if not self.title:
            return fallback
        title, _ = redact(self.title, getattr(self.opts, "private", []))
        return title or fallback

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
            self.count(rec)
            if (kind == "system" and rec.get("subtype") == "turn_duration"
                    and (rec.get("durationMs") or 0) >= TURN_MINUTES * 60000):
                self.turns.append({"session": None, "time": rec.get("timestamp"), "id": rec.get("uuid"),
                                   "minutes": round(rec["durationMs"] / 60000, 1)})
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
                                                       waited_minutes=minutes_between(last_assistant.get("timestamp"), rec.get("timestamp"))))
                    if seen_human:
                        self.events.append(self.moment("correction", rec, excerpt=text))
                    seen_human = True
                    last_assistant = None
                if text is not None or (rec.get("origin") or {}).get("kind") == "peer":
                    self.breaks.add(len(self.calls))  # a new message ends a run of searches
                if rec.get("usageLimitNote"):
                    self.events.append(self.moment("blocked", rec, why="usage_limit", excerpt=plain_text(rec)))
                self.read_results(rec, n, pending)

    def count(self, rec):
        """Adds a record to the session's totals, if it's in the window."""
        t = rec.get("timestamp")
        if t is None or not self.opts.inside(t):
            return
        self.first = self.first or t
        self.last = t
        totals = self.totals
        origin = (rec.get("origin") or {}).get("kind")
        if rec.get("type") == "user":
            if human_text(rec) is not None or origin in ("peer", "task-notification"):
                totals["turns"] += 1
            if not rec.get("toolDenialKind"):  # a refusal isn't an error
                totals["errors"] += sum(1 for b in blocks(rec) if b.get("type") == "tool_result" and b.get("is_error"))
        elif rec.get("type") == "assistant":
            if rec.get("isApiErrorMessage"):
                totals["errors"] += 1
            for b in blocks(rec):
                if b.get("type") == "tool_use":
                    totals["tool_calls"][b.get("name")] = totals["tool_calls"].get(b.get("name"), 0) + 1
        totals["minutes"] = minutes_between(self.first, self.last) or 0

    def read_assistant(self, rec, pending):
        if rec.get("isApiErrorMessage"):
            if rec.get("apiErrorStatus") == 429:
                self.events.append(self.moment("blocked", rec, why="usage_limit", excerpt=plain_text(rec)))
            else:
                self.events.append(self.moment("error", rec, tool=None, excerpt=plain_text(rec)))
            return None
        for b in blocks(rec):
            if b.get("type") == "tool_use":
                inp = b.get("input")
                call = {"name": b.get("name"), "input": inp if isinstance(inp, dict) else {}, "rec": rec, "result": None}
                pending[b.get("id")] = call
                self.calls.append(call)
                if call["name"] in USER_WAIT_TOOLS:
                    call["stop"] = True
        return rec

    def read_results(self, rec, n, pending):
        refused = rec.get("toolDenialKind")
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
                                                   waited_minutes=minutes_between(call["rec"].get("timestamp"), rec.get("timestamp"))))
            if refused:
                # toolDenialKind belongs to the record: one refusal however many results it carries
                self.events.append(self.moment("refusal", rec, how=refused, tool=name, excerpt=text))
                refused = None
                continue
            if rec.get("toolDenialKind"):
                continue
            if not b.get("is_error"):
                continue
            if matches_any(SIGNING, text) or any(s and s.lower() in text.lower() for s in self.opts.signing_errors):
                self.events.append(self.moment("blocked", rec, why="signing", excerpt=text))
            elif matches_any(SIGN_IN, text):
                self.events.append(self.moment("blocked", rec, why="sign_in", excerpt=text))
            elif HOOK_BLOCK.search(text):
                self.unknown_shapes["hook"].append({"session": None, "line": n, "id": rec.get("uuid")})
            else:
                self.events.append(self.moment("error", rec, tool=name, excerpt=(what + " → " if what else "") + first_lines(text)))

    def call_moments(self):
        """Retries, searches and slow calls, from the tool calls in order."""
        # only the calls in the window; a message just before a kept call still ends a search there
        calls, breaks, pending = [], set(), False
        for i, call in enumerate(self.calls):
            pending = pending or i in self.breaks
            if self.opts.inside(call["rec"].get("timestamp")):
                if pending:
                    breaks.add(len(calls))
                    pending = False
                calls.append(call)
        out = []
        groups = {}
        for i, call in enumerate(calls):
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
        for i, call in enumerate(calls + [None]):
            # a run of searches ends at an edit, a new human or peer message, or the end; other tools pass
            if call is not None and i not in breaks:
                if is_search(call):
                    run.append(call)
                if call["name"] not in EDIT_TOOLS:
                    continue
            if len(run) >= SEARCH_MIN:
                end = (run[-1]["result"] or {}).get("rec") or run[-1]["rec"]
                moments.append(self.moment("search", run[0]["rec"], count=len(run),
                                           minutes=minutes_between(run[0]["rec"].get("timestamp"), end.get("timestamp")),
                                           excerpt=summary(run[0]["name"], run[0]["input"]) + " … "
                                           + summary(run[-1]["name"], run[-1]["input"])))
            run = [call] if call is not None and i in breaks and is_search(call) else []
        return moments

    def slow_runs(self):
        """Tool calls at least SLOW_SECONDS long: (group key, run)."""
        out = []
        for call in self.calls:
            if not call["result"]:
                continue
            start, end = call["rec"].get("timestamp"), call["result"]["rec"].get("timestamp")
            seconds = seconds_between(start, end)
            if seconds is None or seconds < SLOW_SECONDS or call["name"] in USER_WAIT_TOOLS:
                continue
            # waits on the user aren't slow steps: a call the user approved, or one left running
            if str((call["result"]["rec"].get("permissionDecision") or {}).get("source", "")).startswith("user"):
                continue
            if call["input"].get("run_in_background"):
                continue
            command = normalise(summary(call["name"], call["input"]), call["rec"].get("cwd"))
            repo = repo_of(call["rec"].get("cwd"), self.opts.repo_map)
            out.append(((command, repo), {"session": self.name, "time": start, "id": call["rec"].get("uuid"),
                                          "minutes": round(seconds / 60, 1),
                                          "last_line": ((call["result"]["text"] or "").strip().splitlines() or [""])[-1]}))
        return out


def normalise(command, cwd=None):
    """The command with whitespace collapsed, and a leading `cd <dir> && ` dropped when it goes to the
    call's own working directory. A cd elsewhere stays: an absolute folder (or one under ~) as written,
    so the same folder is one step whatever the call's cwd; a relative one resolved against the call's
    cwd and written relative to it (./, a trailing / and quotes normalised), so `cd ./frontend` and
    `cd frontend` are one step and `cd frontend` and `cd backend` are two. A ~ is never expanded: it
    would be the home folder of whoever runs the retro, not the session's, and would print their
    username. For the same reason a home folder (/home/<user>, /Users/<user>) is written as ~."""
    command = re.sub(r"\s+", " ", command.strip())
    m = re.match(r"""^cd ("[^"]+"|'[^']+'|\S+) && (.*)$""", command)
    if not m:
        return command
    folder = unquote(m.group(1))
    base = home_as_tilde(os.path.normpath(cwd)) if cwd else None
    if folder.startswith("/") or folder == "~" or folder.startswith("~/") or base is None:
        target = home_as_tilde(os.path.normpath(folder))
        return m.group(2) if target == base else "cd %s && %s" % (target, m.group(2))
    target = os.path.normpath(os.path.join(base, folder))
    if target == base:
        return m.group(2)
    return "cd %s && %s" % (os.path.relpath(target, base), m.group(2))


HOME = re.compile(r"^/(?:home|Users)/[^/]+(?=/|$)|^/root(?=/|$)")


def home_as_tilde(path):
    """The path with a leading home folder written as ~, so it carries no username."""
    return HOME.sub("~", path)


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
        group.sort(key=lambda r: time_key(r["time"]))
        last = group[-1].pop("last_line")
        for r in group[:-1]:
            r.pop("last_line")
        out.append({"kind": "slow", "kind_of": "tool", "command": command, "repo": repo, "runs": group,
                    "count": len(group), "total_minutes": round(sum(r["minutes"] for r in group), 1),
                    "excerpt": last})
    return out


def turn_moments(turns, repo):
    return [{"kind": "slow", "kind_of": "turn", "command": None, "repo": repo, "runs": [t], "count": 1,
             "total_minutes": t["minutes"], "excerpt": "one turn of %s minutes" % t["minutes"]} for t in turns]


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


def strip_comment(line):
    """The line without a YAML comment: a # at the start or after a space, outside quotes."""
    quote = None
    for i, c in enumerate(line):
        if quote:
            quote = None if c == quote else quote
        elif c in "\"'":
            quote = c
        elif c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
    return line


def config_entries(path):
    """(key path, value) for each scalar in a team config, read as text: block mappings, lists, flow
    mappings ({ name: API, url: "…" }) and > or | block scalars. There's no YAML parser in the standard
    library."""
    stack = []
    block = None    # (indent, key path, lines) while reading a > or | block scalar
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for raw in lines + [None]:
        if block is not None:
            if raw is not None and (not raw.strip() or len(raw) - len(raw.lstrip()) > block[0]):
                block[2].append(raw.strip())
                continue
            yield block[1], " ".join(x for x in block[2] if x)
            block = None
        if raw is None:
            break
        line = strip_comment(raw).rstrip()
        if not line.strip():
            continue
        m = re.match(r"^(\s*)(-\s+)?(.*)$", line)
        indent, item, rest = len(m.group(1)), m.group(2), m.group(3)
        if item:
            indent += len(item)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = [k for _, k in stack]
        if rest.startswith("{"):
            for key, value in re.findall(r"([\w-]+)\s*:\s*(\"[^\"]*\"|'[^']*'|[^,}]+)", rest):
                yield parent + [key], unquote(value)
            continue
        km = re.match(r"^([\w.-]+)\s*:(?:\s+(.*))?$", rest)
        if km:
            key, value = km.group(1), (km.group(2) or "").strip()
            if re.fullmatch(r"[>|][+-]?", value):
                block = (indent, parent + [key], [])
            elif value:
                yield parent + [key], unquote(value)
            else:
                stack.append((indent, key))
        elif item:
            yield parent, unquote(rest)


def is_local(value):
    return any(h in value.lower() for h in LOCAL_HOSTS)


def private_values(paths):
    """(value, label) for each identifying value in the configs, longest first. Values of keys named site,
    cloud_id, *_id, host, hostname, domain, url, *_url and test_account_email, plus every URL and its host,
    email domain, IPv4 address and UUID in any value. Never localhost, 127.0.0.1 or 0.0.0.0; nothing under
    4 characters."""
    found = {}

    def add(value, label):
        value = value.strip()
        if len(value) >= 4 and not is_local(value) and value.lower() not in PUBLIC_HOSTS:
            found.setdefault(value, label)
    for path in paths:
        for keys, value in config_entries(path):
            if not keys:
                continue
            key, label = keys[-1], ".".join(keys[-2:])
            if (key in PRIVATE_KEYS or key.endswith(PRIVATE_SUFFIXES)) and value.lower() not in SYMBOLIC_VALUES:
                add(value, label)
            for url in URL.findall(value):
                authority = re.split(r"[/?#]", url.split("://", 1)[1])[0]
                userinfo, _, hostport = authority.rpartition("@")
                host = hostport.split(":")[0]
                if not is_local(host):
                    add(url, label)
                    add(host, label)
                    if ":" in userinfo:  # the password; a user is often a plain word (postgres, admin)
                        add(userinfo.split(":", 1)[1], label)
            for host in HOSTNAME.findall(value):
                if host.rsplit(".", 1)[-1].lower() not in FILE_EXTENSIONS:
                    add(host, label)
            for email in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", value):
                add(email, label)
            for pattern in (EMAIL_DOMAIN, IPV4, UUID):
                for match in pattern.finditer(value):
                    add(match.group(1) if pattern is EMAIL_DOMAIN else match.group(0), label)
    return sorted(found.items(), key=lambda kv: -len(kv[0]))


GIT_CONTEXT = re.compile(r"(?i)\b(?:commit|git|sha|merge|revert|cherry-pick|rebase|HEAD|tree|blob|fixup)\b")


def token_like(piece):
    """A run of letters and digits (separators taken out) that reads as random rather than as words:
    many switches between letters and digits, or mostly one- and two-character pieces when split into
    words (wJalrXUtn…, kQzXwLr…), unlike camelCase names and file names (UsageTableReport2024Final)."""
    if len(piece) < 20:
        return False
    if len(re.findall(r"[A-Za-z](?=\d)|\d(?=[A-Za-z])", piece)) >= 6:
        return True
    words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", piece)
    return len(words) >= 8 and sum(len(w) <= 2 for w in words) / len(words) >= 0.4


def unsure(text):
    """Why a redacted text still can't be trusted, or None: a private key with no end, or a run of 32 or
    more token characters that reads as random. UUIDs are kept, and so is a 40-character hex commit SHA
    when the words before it are about git or it's part of a range (sha..main)."""
    if UNFINISHED_KEY.search(text):
        return "a private key with no end"
    text = UUID.sub(lambda m: " " * len(m.group(0)), text)
    for m in TOKEN_LIKE.finditer(text):
        run = m.group(0)
        if re.fullmatch(r"[0-9a-f]{40}", run):
            if (GIT_CONTEXT.search(text[max(0, m.start() - 30):m.start()])
                    or text[m.end():m.end() + 2] == ".." or text[max(0, m.start() - 2):m.start()] == ".."):
                continue
            return "40 hex characters that aren't a commit"
        if token_like(re.sub(r"[-_=+/]", "", run)):
            return "a long token-like string"
    return None


def whole_word(value):
    """A pattern for the value as a word of its own. A letter at its edge mustn't touch another letter,
    and a digit another digit; `_`, digits next to letters and anything else are word breaks. So host
    acmedb is found in ACMEDB_HOST, acmedb2 and acmedb_replica, but not in acmedbx, and 4821 not in 48210."""
    def edge(c, look):
        if c.isascii() and c.isalpha():
            return "(?%s[A-Za-z])" % look
        return "(?%s[0-9])" % look if c.isdigit() else ""
    return edge(value[0], "<!") + re.escape(value) + edge(value[-1], "!")


def redact(text, private):
    """(redacted text, or None when it can't be cleaned; why not)."""
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    for value, label in private:
        text = re.sub(whole_word(value), "[config: %s]" % label, text, flags=re.I)
    why = unsure(text)
    return (None, why) if why else (text, None)


def redact_moments(found, private):
    summary_ = {"redacted": 0, "dropped": []}
    for m in found:
        if m.get("command"):
            command, why = redact(m["command"], private)
            m["command"] = command if command is not None else "[withheld]"
            if command is None:
                where = m["runs"][-1]
                summary_["dropped"].append({"kind": m["kind"], "session": where["session"], "time": where["time"],
                                            "id": where["id"], "reason": why, "field": "command"})
        if m.get("excerpt") is None:
            continue
        text, why = redact(m["excerpt"], private)
        if text is None:
            m["excerpt"], m["excerpt_dropped"] = None, True
            where = m["runs"][-1] if m.get("runs") else m
            summary_["dropped"].append({"kind": m["kind"], "session": where["session"], "time": where["time"],
                                        "id": where["id"], "reason": why})
        else:
            if text != m["excerpt"]:
                summary_["redacted"] += 1
            m["excerpt"] = trim(text)
    return summary_


def moments(opts):
    sessions, unparseable, unreadable = [], [], []
    for path in opts.transcripts:
        s = Session(path, opts)
        try:
            s.read()
        except OSError as e:  # one unreadable transcript doesn't stop the others
            unreadable.append({"session": s.name, "path": path,
                               "reason": "can't read the file: %s" % (e.strerror or e)})
            continue
        sessions.append(s)
    out_moments, slow, turn_slow, unknown_types = [], [], [], {}
    shapes = {"hook": [], "delivery": []}
    for s in sessions:
        for m in s.events + s.call_moments():
            m["session"] = s.name
            if opts.inside(m["time"]):
                out_moments.append(m)
        slow += [(key, r) for key, r in s.slow_runs() if opts.inside(r["time"])]
        turns = [dict(t, session=s.name) for t in s.turns if opts.inside(t["time"])]
        for u in s.unparseable:
            unparseable.append(dict(u, session=s.name))
        for k, v in s.unknown_types.items():
            unknown_types[k] = unknown_types.get(k, 0) + v
        for k in shapes:
            shapes[k] += [dict(x, session=s.name) for x in s.unknown_shapes[k]]
        turn_slow += turn_moments(turns, repo_of(s.cwd, opts.repo_map))
    slow_moments = sorted(group_slow(slow) + turn_slow, key=lambda m: -m["total_minutes"])
    redaction = redact_moments(slow_moments + out_moments, opts.private)
    out_moments.sort(key=lambda m: time_key(m["time"]))
    return {
        "window": [opts.since, opts.until],
        "sessions": [{"session": s.name, "id": s.id, "path": s.path, "repo": repo_of(s.cwd, opts.repo_map),
                      "totals": s.totals} for s in sessions],
        "moments": slow_moments + out_moments,
        "unreadable": unreadable,
        "unparseable": unparseable,
        "unknown_types": unknown_types,
        "unknown_shapes": shapes,
        "subagents_not_read": subagent_count(opts.transcripts),
        "redaction": redaction,
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
    r = sub.add_parser("redact", help="the text on stdin with secrets and config values taken out")
    r.add_argument("--config", action="append", default=[], metavar="FILE")
    opts = parser.parse_args(argv)
    if opts.command == "redact":
        return opts
    since, until = parse_time(opts.since), parse_time(opts.until)
    for name, given, parsed in (("--since", opts.since, since), ("--until", opts.until, until)):
        if given and parsed is None:
            parser.error("%s takes an ISO time, not %r" % (name, given))

    def inside(value):
        """True when a time is in the window; with no window, always. A record with no time is outside a window."""
        if since is None and until is None:
            return True
        t = parse_time(value)
        return t is not None and (since is None or t >= since) and (until is None or t <= until)
    opts.inside = inside
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
        opts.private = private_values(opts.config)
        if opts.command == "redact":
            text, why = redact(sys.stdin.read(), opts.private)
            result = {"text": text, "dropped": text is None, "reason": why}
        else:
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
