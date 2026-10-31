#!/usr/bin/env python3
"""Reads a run's Claude Code transcripts for the retro skill and prints one JSON object.

  moments TRANSCRIPT... [--since ISO] [--until ISO] [--config FILE]... [--repo-of PATH=REPO]...
      The moments worth a finding (corrections, refusals, errors, retries, long searches,
      slow steps, stops for the user, blocks), with totals per session; a transcript that
      can't be opened is listed in "unreadable" and the others are still read.
  redact [--config FILE]...      (text on stdin)
      The text with secrets and the team config's identifying values taken out.
  check [FILE] [--config FILE]... [--cwd PATH]... [--transcript FILE]... [--no-users]   (or stdin)
      Before a draft leaves the machine: each full path, configured value, username (from the
      cwds and the transcripts' records) and secret it would take out, and a token-like string
      redact would withhold, by line, column and length, never the text itself. Exit 3 when
      there's any; exit 4, with a reason, when it can't check: a transcript it can't open, or
      no usernames to look for (unless --no-users).

Every quote it prints is redacted: generic secrets by pattern, then each identifying value in
the team config and its overrides (--config, in roost-config's order). A quote it can't clean
with confidence is dropped, and its moment kept.

Exit 0 whatever it finds (unreadable records are in the JSON; check exits 3 when a draft
has something to take out, and 4 when it can't check), 2 for bad arguments, 1 for a failure of its own, with {"error": "<type>: <message>"}.

Standard library only. Run it from the skill's own folder: <skill folder>/scripts/.
"""
import argparse
import datetime
import glob
import json
import math
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
# `cd <folder> && ` as written: a quoted folder, $(…), one with escaped spaces (My\ Project), or none (cd)
CD_PREFIX = r"""cd(?: (?:"[^"]*"|'[^']*'|\$\([^)]*\)|(?:\\.|[^\s\\])+))? && """
READ_ONLY_BASH = re.compile(r"""^(?!(?:[^'"]|'[^']*'|"[^"]*")*?(?:<<|(?<![2&])>(?!&)))(?:""" + CD_PREFIX + r""")?(?:grep|rg|find|ls|cat|head|tail|sed -n|wc|git (?:log|show|grep|diff|status))\b""", re.S)
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
USER_WAIT_TOOLS = {"AskUserQuestion"}
NOT_TYPED = ("<command-", "<local-command-", "<bash-", "<system-reminder>", "<task-notification",
             "<cross-session-message", "[Cross-session ")
SIGNING = [re.compile(p, re.I) for p in (r"gpg failed to sign", r"failed to sign the data", r"error: signing failed")]
SIGN_IN = [re.compile(p, re.I) for p in (r"gh auth login", r"not logged in", r"HTTP 401", r"authentication required")]
HOOK_BLOCK = re.compile(r"\bhook\b.*\b(?:block|blocked|denied|deny)\b|\b(?:block|blocked|denied)\b.*\bhook\b", re.I | re.S)
REJECTED_INTERRUPTION = "[Request interrupted by user for tool use]"   # written after a rejected prompt
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
    """Yields (line number, record, None, cwd) for each JSON line, and (line number, None, reason, cwd) for each
    it can't read. cwd is the line's own cwd when it's text, even on a line that can't be read, so its
    username is still known."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            rec, why = read_line(line, last=n == len(lines) and not line.endswith("\n"))
        except Exception:  # anything else about a line (a number too big to compare) lists it alone
            rec, why = None, "fields of an unexpected type"
        yield n, (None if why else rec), why, line_cwd(line)


def line_cwd(line):
    """A line's cwd when it's JSON with a cwd that's text, or None."""
    try:
        cwd = json.loads(line).get("cwd")
    except Exception:
        return None
    return cwd if isinstance(cwd, str) else None


def read_line(line, last):
    """(record, None), or (None, why it can't be read)."""
    try:
        rec = json.loads(line)
    except ValueError:
        return None, "incomplete last line (still being written?)" if last else "not JSON"
    if not isinstance(rec, dict):
        return None, "not a JSON object"
    why = wrong_types(rec)
    if why:
        return None, why
    if rec.get("type") in ("user", "assistant"):
        if not isinstance(rec.get("message"), dict):
            return None, "missing message"
        if not isinstance(rec["message"].get("content"), (str, list, type(None))):
            return None, "unsupported message content"
    return rec, None


TOOL_TEXT_INPUTS = ("command", "file_path", "pattern", "path", "url", "query")


def wrong_types(rec):
    """Why a record's fields can't be read (a field of the wrong type), or None. A record listed for this
    is skipped whole: nothing of it is counted."""
    def text_or_none(*values):
        return all(isinstance(v, (str, type(None))) for v in values)
    if not text_or_none(rec.get("type")):
        return "a type that isn't text"
    if not text_or_none(rec.get("cwd")):
        return "a cwd that isn't text"
    if not text_or_none(rec.get("sessionId")):
        return "a session id that isn't text"
    if not text_or_none(rec.get("uuid"), rec.get("parentUuid")):
        return "a record id that isn't text"
    if not text_or_none(rec.get("timestamp")):
        return "a time that isn't text"
    if not text_or_none(rec.get("customTitle"), rec.get("agentName")):
        return "a title that isn't text"
    if not isinstance(rec.get("permissionDecision"), (dict, type(None))):
        return "a permission decision that isn't an object"
    duration = rec.get("durationMs")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, (int, float))
                                 or not math.isfinite(duration)):
        return "a duration that isn't a number"
    content = (rec.get("message") or {}).get("content") if isinstance(rec.get("message"), dict) else None
    for b in content if isinstance(content, list) else []:
        if not isinstance(b, dict):
            continue
        if not text_or_none(b.get("text")):
            return "a text that isn't text"
        if b.get("type") == "tool_use":
            if not isinstance(b.get("name"), str):
                return "a tool name that isn't text"
            if not text_or_none(b.get("id")):
                return "a tool call id that isn't text"
            inp = b.get("input") if isinstance(b.get("input"), dict) else {}
            if not text_or_none(*(inp.get(k) for k in TOOL_TEXT_INPUTS)):
                return "a tool input that isn't text"
            questions = inp.get("questions")
            if questions is not None and (not isinstance(questions, list) or any(
                    not isinstance(q, dict) or not isinstance(q.get("question", ""), str) for q in questions)):
                return "a question that isn't text"
        if b.get("type") == "tool_result":
            if not text_or_none(b.get("tool_use_id")):
                return "a tool call id that isn't text"
            if not isinstance(b.get("content"), (str, list, type(None))):
                return "a tool result that isn't text or a list"
            for c in b["content"] if isinstance(b.get("content"), list) else []:
                if isinstance(c, dict) and not text_or_none(c.get("text")):
                    return "a text that isn't text"
    return None


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
    if cwd and HOME_FOLDER.fullmatch(cwd.rstrip("/\\")):
        return "[home]"  # the folder's name is a username
    return re.split(r"[/\\]", (cwd or "").rstrip("/\\"))[-1] or None


# A home folder: /Users/<name>, /home/<name>, /var/home/<name> or /root, also under WSL's /mnt/<drive>, and
# a Windows drive's Users\<name>.
HOME_FOLDER = re.compile(r"(?:/mnt/[a-z])?(?:/Users/[^/\\]+|/home/[^/\\]+|/var/home/[^/\\]+|/root)"
                         r"|[A-Za-z]:[\\/]+Users[\\/]+[^/\\]+")
# A full path: a token that starts with / and has a second / or \ in it (/home/x, not /compact), ~ with a
# name or a folder (~/x, ~bob/x; not a bare ~), ../, a drive (C:\ or C:/), \\server or \\?\, JSON's \/, a
# project folder's name (-Users-<name>-…, -home-<name>-…), or a URL whose scheme isn't a web or database
# one (file://, vscode://). Also a quoted path, spaces and all, a web URL serving a home folder's file
# (/@fs/Users/…) and a URL-encoded home path (%2FUsers%2F…). It starts wherever it sits: after a space, a
# quote, =, >, |, @, {, _, : (PATH=$PATH:/x, but not a URL's ://), < before a path (not </div>), a glued flag
# (-I/x), an escaped \n, \r or \t, or a colour code. A / inside a word (src/a.ts, w/o, 1/2) doesn't start one.
PATH_CHARS = r"""[^\s"'`<>|;,()\[\]{}\x1b]"""   # a colour code (\x1b[0m) ends a path too
WEB_SCHEMES = r"(?:https?|wss?|s?ftp|ssh|git|postgres(?:ql)?|mysql|redis|mongodb(?:\+srv)?|amqps?)"
FULL_PATH = re.compile(
    # a quoted path, spaces and all ('/home/x/My Config/a.yml')
    r"""(?<=(?P<q>['"`]))(?=/[^'"`\n]*/|~[\w.-]*/|[A-Za-z]:[\\/]|\\\\)[^'"`\n]+?(?=(?P=q))"""
    # a web URL serving a home folder's file (Vite's /@fs/Users/…), and a URL-encoded home path
    r"""|(?<![A-Za-z0-9+.-])%(w)s://[^\s"'`<>|;,()\[\]{}]*?/(?:@fs/)?(?:Users|home)/%(c)s*|(?i:%%2F(?:Users|home)%%2F)%(c)s*"""
    r"""|(?<![A-Za-z0-9+.-])(?!%(w)s://)[A-Za-z][A-Za-z0-9+.-]*://%(c)s*"""
    r"""|(?:(?<=[\s"'=]-[A-Za-z])|(?<=\\[nrt])|(?<=:)(?!//)|(?<=<)(?=/%(c)s*/|[A-Za-z]:[\\/]|\\\\)"""
    r"""|(?<=\x1b\[\dm)|(?<=\x1b\[\d\dm)|(?<=\x1b\[\d;\d\dm)|(?<![A-Za-z0-9.~$/\\<:-]))"""
    r"""(?:[A-Za-z]:[\\/]%(c)s*|\\\\[A-Za-z0-9?.]%(c)s*|/(?=%(c)s*[/\\])%(c)s+|\\/(?=%(c)s*\\/)%(c)s+"""
    r"""|\.\.[\\/]%(c)s*|-(?:Users|home)-%(c)s*|~(?:[A-Za-z_][\w.-]*)?[\\/]%(c)s*"""
    r"""|~[A-Za-z_][\w.-]*(?=[\s"'`<>|;,()\[\]{}]|$))"""
    % {"c": PATH_CHARS, "w": WEB_SCHEMES})


# The username in a home folder at the start of a cwd, or at the start of a project folder's name.
CWD_USER = re.compile(r"^(?:/mnt/[a-z])?(?:/Users|/home|/var/home)/([^/\\]+)|^[A-Za-z]:[\\/]+Users[\\/]+([^/\\]+)")
# Accounts many people share (CI runners, containers, cloud images): their names are ordinary words too.
SHARED_ACCOUNTS = {"shared", "guest", "node", "runner", "ubuntu", "ec2-user", "vscode", "codespace", "admin",
                   "user", "app", "dev", "docker", "root"}
FOLDER_USER = re.compile(r"^-(?:Users|home)-([^-]+)")


def usernames(cwds, transcripts):
    """The usernames in the sessions' home folders: from each cwd, and from each transcript's project folder
    name (its first word only: a - in the name can't be told from a /). Never a shared account's name
    (SHARED_ACCOUNTS), nor one under 3 characters."""
    found = set()
    for cwd in cwds:
        m = CWD_USER.match(cwd or "")
        if m:
            found.add(m.group(1) or m.group(2))
    for path in transcripts:
        m = FOLDER_USER.match(os.path.basename(os.path.dirname(os.path.abspath(path))))
        if m:
            found.add(m.group(1))
    # longest first, so quillon.zephyrine is replaced whole before quillon (from its project folder) is
    return sorted((u for u in found if len(u) >= 3 and u.lower() not in SHARED_ACCOUNTS), key=lambda u: (-len(u), u))


def apply_spans(text, spans):
    """The text with each (start, end, replacement) span replaced; the spans don't overlap."""
    for start, end, replacement in sorted(spans, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def path_spans(text):
    """(start, end) of every full path. Punctuation that ends a sentence after a path isn't part of it."""
    return [(m.start(), m.start() + len(m.group(0).rstrip(".,:;?!"))) for m in FULL_PATH.finditer(text)]


def strip_paths(text):
    """The text with every full path written as [path]."""
    return apply_spans(text, [(a, b, "[path]") for a, b in path_spans(text)])


ISO_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?")


def scrub(value, users=(), private=()):
    """The last pass over everything the script prints, every string and every key (tool names, the
    tool_calls keys, the error object): each configured value becomes [config: <key>], each full path
    [path] and each session's username, as a word of its own, [user]. So no configured value, folder,
    home or username is printed. A repo-relative path (src/a.ts) stays."""
    if isinstance(value, str):
        if ISO_TIME.fullmatch(value):  # a record's time, never a quote
            return value
        return replace_users(replace_config(strip_paths(value), private), users)  # paths first, as in redact()
    if isinstance(value, list):
        return [scrub(v, users, private) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            k, v = scrub(k, users, private), scrub(v, users, private)
            # two names that redact alike (two configured MCP servers) are one key: add up their counts
            out[k] = out[k] + v if isinstance(out.get(k), int) and isinstance(v, int) else out.get(k, v)
        return out
    return value


class Session:
    """One transcript read into what the moments need."""

    def __init__(self, path, opts):
        self.path = path
        self.opts = opts
        self.id = None
        self.title = None
        self.cwd = None
        self.cwds = set()       # every cwd its records name, for the usernames in them
        self.events = []        # (time, moment) found in this transcript, before the window
        self.calls = []         # tool calls in order: dicts with name, input, id, time, result info
        self.unparseable = []
        self.unknown_types = {}
        self.unknown_shapes = {"hook": [], "delivery": []}
        self.breaks = set()     # positions in calls where a human or peer message came in
        self.turns = []         # turns at least TURN_MINUTES long
        self.totals = {"turns": 0, "tool_calls": {}, "errors": 0, "minutes": 0}
        self.first = self.last = None   # first and last timestamped record in the window
        self._name = None
        self._repos = {}        # cwd -> its repo, redacted

    @property
    def name(self):
        """The session's title, redacted like any quote, or the start of its id (or of its file's name,
        redacted like a path). Worked out once, on first use after the transcript is read."""
        if self._name is None:
            private = getattr(self.opts, "private", [])
            title = redact(self.title, private)[0] if self.title else None
            self._name = title or redact_path((self.id or os.path.basename(self.path))[:8], private)
        return self._name

    def repo(self, cwd):
        """The repo a cwd is in, redacted once per cwd: a repo named after its folder can hold a configured
        value."""
        if cwd not in self._repos:
            name = repo_of(cwd, self.opts.repo_map)
            self._repos[cwd] = name and redact_path(name, getattr(self.opts, "private", []))
        return self._repos[cwd]

    def moment(self, kind, rec, **fields):
        return dict({"kind": kind, "session": None, "time": rec.get("timestamp"), "id": rec.get("uuid")}, **fields)

    def read(self):
        pending = {}
        seen_human = False
        last_assistant = None
        after_refusal = False   # a user-rejected refusal with no assistant record or typed message since
        for n, rec, reason, cwd in records(self.path):
            if cwd:  # its username is known even when the record can't be read
                self.cwds.add(cwd)
            saved = self.save(pending, (seen_human, last_assistant, after_refusal))
            try:
                if rec is None:
                    self.unparseable.append({"session": None, "line": n, "reason": reason})
                    continue
                kind = rec.get("type")
                if kind not in KNOWN_TYPES:
                    self.unknown_types[kind] = self.unknown_types.get(kind, 0) + 1
                    continue
                # rejecting a permission prompt also writes an interruption: one refusal, not a correction or a turn too
                echo = kind == "user" and after_refusal and human_text(rec) == REJECTED_INTERRUPTION
                if (kind == "system" and rec.get("subtype") == "turn_duration"
                        and (rec.get("durationMs") or 0) >= TURN_MINUTES * 60000):
                    self.turns.append({"session": None, "time": rec.get("timestamp"), "id": rec.get("uuid"),
                                       "minutes": round(rec["durationMs"] / 60000, 1)})
                if kind == "system" and rec.get("subtype") == "stop_hook_summary" and rec.get("preventedContinuation"):
                    self.unknown_shapes["hook"].append({"session": None, "line": n, "id": rec.get("uuid")})
                if kind == "assistant":
                    last_assistant = self.read_assistant(rec, pending) or last_assistant
                    after_refusal = False
                elif kind == "user":
                    text = human_text(rec)
                    if DELIVERY.search(plain_text(rec)):
                        self.unknown_shapes["delivery"].append({"session": None, "line": n, "id": rec.get("uuid")})
                    if text is not None and not echo:   # the user's answer is still to come
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
                    if rec.get("toolDenialKind") == "user-rejected":
                        after_refusal = True
                    elif text is not None:   # another call's result between them doesn't end it
                        after_refusal = False
                # last, so a record that fails on the way is neither counted nor names the session
                if kind == "custom-title" and rec.get("customTitle"):
                    self.title = rec["customTitle"]
                elif kind == "agent-name" and rec.get("agentName") and not self.title:
                    self.title = rec["agentName"]
                self.id = self.id or rec.get("sessionId")
                self.cwd = self.cwd or rec.get("cwd")
                if rec.get("cwd"):
                    self.cwds.add(rec["cwd"])
                self.count(rec, echo)
            except Exception:  # a shape wrong_types() doesn't know: list it, and undo all it did
                seen_human, last_assistant, after_refusal = self.restore(saved, pending)
                self.unparseable.append({"session": None, "line": n, "reason": "fields of an unexpected type"})

    def count(self, rec, echo=False):
        """Adds a record to the session's totals, if it's in the window. `echo` is the interruption a
        rejected prompt writes, which isn't a turn of its own."""
        t = rec.get("timestamp")
        if t is None or not self.opts.inside(t):
            return
        self.first = self.first or t
        self.last = t
        totals = self.totals
        origin = (rec.get("origin") or {}).get("kind")
        if rec.get("type") == "user":
            if not echo and (human_text(rec) is not None or origin in ("peer", "task-notification")):
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

    def save(self, pending, local):
        """Everything one record can change, to put back if reading it fails partway."""
        return {"local": local, "pending": dict(pending), "events": len(self.events), "calls": len(self.calls),
                "turns": len(self.turns), "shapes": {k: len(v) for k, v in self.unknown_shapes.items()},
                "unparseable": len(self.unparseable), "unknown_types": dict(self.unknown_types),
                "breaks": set(self.breaks), "cwds": set(self.cwds),
                "totals": dict(self.totals, tool_calls=dict(self.totals["tool_calls"])),
                "scalars": (self.title, self.id, self.cwd, self.first, self.last)}

    def restore(self, saved, pending):
        """Puts back what save() kept, and returns the loop's own state."""
        for call in saved["pending"].values():  # a call still waiting had no result before this record
            call["result"] = None
        pending.clear()
        pending.update(saved["pending"])
        del self.events[saved["events"]:], self.calls[saved["calls"]:], self.turns[saved["turns"]:]
        del self.unparseable[saved["unparseable"]:]
        for k, n in saved["shapes"].items():
            del self.unknown_shapes[k][n:]
        self.unknown_types, self.breaks, self.cwds = saved["unknown_types"], saved["breaks"], saved["cwds"]
        self.totals = saved["totals"]
        self.title, self.id, self.cwd, self.first, self.last = saved["scalars"]
        return saved["local"]

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
                # everything later passes need from the call, worked out now, so a call that can't be read
                # fails with its record
                call["what"] = summary(call["name"], call["input"])
                call["key"] = (call["name"], json.dumps(call["input"], sort_keys=True))
                call["search"] = is_search(call)
                call["step"] = FULL_PATH.sub("[path]", normalise(call["what"]))  # grouped as printed
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
            what = call["what"] if call else ""
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
            key = call["key"]
            g = groups.get(key)
            if g and g["last"] >= i - RETRY_WINDOW:
                g["count"] += 1
                g["last"] = i
            else:
                groups[key] = g = {"first": call, "count": 1, "last": i}
                out.append(g)
        moments = [self.moment("retry", g["first"]["rec"], tool=g["first"]["name"], count=g["count"],
                               excerpt=g["first"]["what"]) for g in out if g["count"] > 1]
        run = []
        for i, call in enumerate(calls + [None]):
            # a run of searches ends at an edit, a new human or peer message, or the end; other tools pass
            if call is not None and i not in breaks:
                if call["search"]:
                    run.append(call)
                if call["name"] not in EDIT_TOOLS:
                    continue
            if len(run) >= SEARCH_MIN:
                end = (run[-1]["result"] or {}).get("rec") or run[-1]["rec"]
                moments.append(self.moment("search", run[0]["rec"], count=len(run),
                                           minutes=minutes_between(run[0]["rec"].get("timestamp"), end.get("timestamp")),
                                           excerpt=run[0]["what"] + " … " + run[-1]["what"]))
            run = [call] if call is not None and i in breaks and call["search"] else []
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
            repo = self.repo(call["rec"].get("cwd"))
            out.append(((call["step"], repo), {"session": self.name, "time": start, "id": call["rec"].get("uuid"),
                                          "minutes": round(seconds / 60, 1),
                                          "last_line": ((call["result"]["text"] or "").strip().splitlines() or [""])[-1]}))
        return out


def normalise(command):
    """The command with whitespace collapsed and any leading `cd <dir> && ` dropped, so the folder it ran in
    is never printed and one command is one step wherever it ran in the repo."""
    command = re.sub(r"\s+", " ", command.strip())
    while True:
        m = re.match("^" + CD_PREFIX + "(.*)$", command)
        if not m:
            return command
        command = m.group(1)


def is_search(call):
    if call["name"] in SEARCH_TOOLS:
        return True
    return call["name"] == "Bash" and bool(READ_ONLY_BASH.match(call["input"].get("command", "")))


def group_slow(runs, private=(), users=()):
    """Slow runs grouped by command and repo, the command as it will print: a configured value or a
    username however it was written (acmedb, ACMEDB) is one step."""
    groups = {}
    for (command, repo), run in runs:
        groups.setdefault((replace_users(replace_config(command, private), users), repo), []).append(run)
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
    # each value also as Claude Code and MCP write it in names: every character but a letter or digit as
    # - (a project folder, acme-example-com) or _ (an MCP server, mcp__acme_example_com__query)
    for value, label in list(found.items()):
        if re.search(r"[^A-Za-z0-9]", value):
            for sep in "-_":
                found.setdefault(re.sub(r"[^A-Za-z0-9]", sep, value), label)
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


def unsure_span(text):
    """(why, start, end) for the first part of a redacted text that still can't be trusted, or None: a
    private key with no end, or a run of 32 or more token characters that reads as random. UUIDs are
    kept, and so is a 40-character hex commit SHA when the words before it are about git or it's part of
    a range (sha..main)."""
    m = UNFINISHED_KEY.search(text)
    if m:
        return "a private key with no end", m.start(), m.end()
    text = UUID.sub(lambda m: " " * len(m.group(0)), text)
    for m in TOKEN_LIKE.finditer(text):
        run = m.group(0)
        if re.fullmatch(r"[0-9a-f]{40}", run):
            if (GIT_CONTEXT.search(text[max(0, m.start() - 30):m.start()])
                    or text[m.end():m.end() + 2] == ".." or text[max(0, m.start() - 2):m.start()] == ".."):
                continue
            return "40 hex characters that aren't a commit", m.start(), m.end()
        if token_like(re.sub(r"[-_=+/]", "", run)):
            return "a long token-like string", m.start(), m.end()
    return None


def unsure(text):
    """Why a redacted text still can't be trusted, or None (see unsure_span)."""
    found = unsure_span(text)
    return found and found[0]


def whole_word(value):
    """A pattern for the value as a word of its own. A value made only of digits mustn't touch a letter or
    a digit on either side, so board id 4821 is found in `board 4821`, `id=4821` and `board_4821` but not
    inside a commit SHA; redact() also leaves it alone as a group of a UUID (a session id). Otherwise a letter at its edge mustn't touch another letter, and
    a digit another digit; `_`, digits next to letters and anything else are word breaks. So host acmedb
    is found in ACMEDB_HOST, acmedb2 and acmedb_replica, but not in acmedbx."""
    if value.isdigit():
        return r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(value)

    def edge(c, look):
        if c.isascii() and c.isalpha():
            return "(?%s[A-Za-z])" % look
        return "(?%s[0-9])" % look if c.isdigit() else ""
    return edge(value[0], "<!") + re.escape(value) + edge(value[-1], "!")


DATE_OR_TIME = re.compile(r"\d{4}-\d{2}-\d{2}(?:T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?")


def mask(text, spans):
    """The text with each span blanked out (as NULs, which are no letter, digit or path character), so a
    later search sees a replaced part as a word break and never matches inside it, as if it had been
    replaced, while every position stays the same."""
    for start, end, *_ in spans:
        text = text[:start] + MASK * (end - start) + text[end:]
    return text


MASK = "\x00"


def config_spans(text, private):
    """(start, end, key) of each configured value as a word of its own, longest values first, each value
    looked for with the earlier ones already taken out (so 4821 next to a replaced acmedb is still a word);
    a number is never a group of a session id or other UUID, nor part of a time or a date."""
    found = []
    skip = [m.span() for m in UUID.finditer(text)] + [m.span() for m in DATE_OR_TIME.finditer(text)]
    for value, label in private:
        masked = mask(text, found)
        if value.isdigit():
            matches = [m for m in re.finditer(whole_word(value), masked)
                       if not any(a <= m.start() < b for a, b in skip)]
        else:
            matches = list(re.finditer(whole_word(value), masked, flags=re.I))
        found += [(m.start(), m.end(), label) for m in matches]
    return found


def replace_config(text, private):
    """The text with each configured value, as a word of its own, written as [config: <key>]."""
    return apply_spans(text, [(a, b, "[config: %s]" % label) for a, b, label in config_spans(text, private)])


def redact(text, private):
    """(redacted text, or None when it can't be cleaned; why not)."""
    for pattern, replacement in SECRET_PATTERNS:
        text = pattern.sub(replacement, text)
    text = replace_config(strip_paths(text), private)  # paths first: a [..] inside one would end it
    why = unsure(text)
    return (None, why) if why else (text, None)


def redact_path(path, private):
    """A transcript's file name (or a path), redacted like a quote, one part at a time (private_values()
    also gives each value as Claude Code writes it in a folder's name: acme.example.com as
    acme-example-com). A part that can't be cleaned (a random temporary folder's name) is withheld alone.
    The output prints only a transcript's file name: its folders hold the session's cwd and the reader's
    home."""
    return "/".join(redact(part, private)[0] or "[withheld]" if part else part for part in path.split("/"))


def user_spans(text, users):
    """(start, end) of each username as a word of its own, longest first."""
    found = []
    for user in users:
        found += [m.span() for m in re.finditer(whole_word(user), mask(text, found), flags=re.I)]
    return found


def replace_users(text, users):
    """The text with each username, as a word of its own, written as [user]."""
    return apply_spans(text, [(a, b, "[user]") for a, b in user_spans(text, users)])


def check(text, private, users):
    """What would be taken out of a draft before it leaves the machine (a ticket, a task), by the last
    pass's rules and redact()'s together: each full path, configured value, username and generic secret,
    in the order the last pass takes them, and the first token-like string redact() would withhold
    (`unsure`, with its reason). Each with its line, column and length, never the text it found: a
    configured value is named by its key."""
    taken = [(a, b, "path", None) for a, b in path_spans(text)]
    taken += [(a, b, "config", key) for a, b, key in config_spans(mask(text, taken), private)]
    taken += [(a, b, "user", None) for a, b in user_spans(mask(text, taken), users)]
    for pattern, _ in SECRET_PATTERNS:
        taken += [(m.start(), m.end(), "secret", None) for m in pattern.finditer(mask(text, taken))
                  if MASK not in m.group(0)]
    left = unsure_span(mask(text, taken))
    if left:
        taken.append((left[1], left[2], "unsure", left[0]))
    if not taken and scrub(text, users, private) != text:  # the pass changed something no span shows
        taken = [(0, len(text), "other", None)]
    hits = []
    for start, end, kind, detail in sorted(taken):
        line = text.count("\n", 0, start) + 1
        hit = {"kind": kind, "line": line, "column": start - (text.rfind("\n", 0, start) + 1) + 1, "length": end - start}
        if detail:
            hit["key" if kind == "config" else "reason"] = detail
        hits.append(hit)
    return {"passed": not hits, "hits": hits}


def transcript_cwds(paths):
    """(every cwd the transcripts' records name, how many transcripts couldn't be opened)."""
    cwds, missing = set(), 0
    for path in paths:
        try:
            cwds.update(cwd for _, _, _, cwd in records(path) if cwd)
        except OSError:
            missing += 1
    return cwds, missing


def redact_moments(found, private, users=()):
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
            # before the cut, which could split a name; paths first, since a [user] inside one would end it
            m["excerpt"] = trim(replace_users(strip_paths(text), users))
    return summary_


def moments(opts):
    sessions, unparseable, unreadable = [], [], []
    for path in opts.transcripts:
        s = Session(path, opts)
        try:
            s.read()
            # everything this transcript adds, worked out before any of it is kept
            found = [m for m in s.events + s.call_moments() if opts.inside(m["time"])]
            for m in found:
                m["session"] = s.name
            s.found = (found, [(key, r) for key, r in s.slow_runs() if opts.inside(r["time"])],
                       turn_moments([dict(t, session=s.name) for t in s.turns if opts.inside(t["time"])], s.repo(s.cwd)))
        except Exception as e:  # one transcript that can't be read doesn't stop the others
            # by its short id only: a title is in the file. The reason never carries the path.
            reason = ("can't read the file: %s" % (e.strerror or type(e).__name__) if isinstance(e, OSError)
                      else "couldn't be read: %s" % type(e).__name__)
            s._name = None
            s.title = None
            unreadable.append({"session": s.name, "path": redact_path(os.path.basename(path), opts.private),
                               "reason": reason})
            continue
        sessions.append(s)
    out_moments, slow, turn_slow, unknown_types = [], [], [], {}
    shapes = {"hook": [], "delivery": []}
    for s in sessions:
        found, runs, turns = s.found
        out_moments += found
        slow += runs
        turn_slow += turns
        for u in s.unparseable:
            unparseable.append(dict(u, session=s.name))
        for k, v in s.unknown_types.items():
            unknown_types[k] = unknown_types.get(k, 0) + v
        for k in shapes:
            shapes[k] += [dict(x, session=s.name) for x in s.unknown_shapes[k]]
    opts.users = usernames(set().union(*[s.cwds for s in sessions]), opts.transcripts)
    slow_moments = sorted(group_slow(slow, opts.private, opts.users) + turn_slow, key=lambda m: -m["total_minutes"])
    redaction = redact_moments(slow_moments + out_moments, opts.private, opts.users)
    out_moments.sort(key=lambda m: time_key(m["time"]))
    return {
        "window": [opts.since, opts.until],
        "sessions": [{"session": s.name, "id": s.id, "path": redact_path(os.path.basename(s.path), opts.private), "repo": s.repo(s.cwd),
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
    c = sub.add_parser("check", help="what the last pass would change in a draft (a file, or stdin)")
    c.add_argument("draft", nargs="?", metavar="FILE")
    c.add_argument("--config", action="append", default=[], metavar="FILE")
    c.add_argument("--cwd", action="append", default=[], metavar="PATH", help="a session's cwd, for its username")
    c.add_argument("--transcript", action="append", default=[], metavar="FILE", help="a run's transcript, for its usernames")
    c.add_argument("--no-users", action="store_true", help="check without usernames (there's no session to name one)")
    opts = parser.parse_args(argv)
    if opts.command in ("redact", "check"):
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
        elif opts.command == "check":
            if opts.draft:
                with open(opts.draft, encoding="utf-8") as f:
                    text = f.read()
            else:
                text = sys.stdin.read()
            cwds, missing = transcript_cwds(opts.transcript)
            opts.users = usernames(set(opts.cwd) | cwds, opts.transcript)
            # fail closed: a check that doesn't know whose name to look for can't pass a draft
            if missing:
                # --no-users or not: a transcript given that can't be opened is a mistake to fix
                result = {"passed": False, "hits": [], "reason": "can't open a transcript (%d of %d): check the "
                          "paths and pass the run's transcripts" % (missing, len(opts.transcript))}
            elif not opts.users and not opts.no_users:
                result = {"passed": False, "hits": [], "reason": "no usernames to check for: pass the run's "
                          "--transcript or the session's --cwd (a home folder), or --no-users"}
            else:
                result = check(text, opts.private, opts.users)
        else:
            opts.signing_errors = read_config_lists(opts.config, "signing_errors")
            result = moments(opts)
        code = (4 if result.get("reason") else 3) if opts.command == "check" and not result["passed"] else 0
    except Exception as e:  # its own failure: say what, never a traceback
        result, code = {"error": "%s: %s" % (type(e).__name__, e)}, 1
        if not hasattr(opts, "private"):  # a config couldn't be read: the values of those that can
            try:
                opts.private = private_values([p for p in opts.config if os.path.isfile(p)])
            except Exception:
                opts.private = []
    try:
        out = scrub(result, getattr(opts, "users", ()), opts.private)
    except Exception as e:  # never a traceback, even from the last pass
        out, code = {"error": "%s: the output couldn't be cleaned" % type(e).__name__}, 1
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
