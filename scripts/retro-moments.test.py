#!/usr/bin/env python3
"""Tests skills/retro/scripts/retro_moments.py with synthetic transcripts only:
the fixtures in scripts/fixtures/retro-moments/ and transcripts built here. No real
transcript is ever committed.

Run: python3 scripts/retro-moments.test.py
"""
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "retro", "scripts", "retro_moments.py")
FIXTURES = os.path.join(ROOT, "scripts", "fixtures", "retro-moments")
sys.path.insert(0, os.path.dirname(SCRIPT))

import retro_moments  # noqa: E402

SID = "00000000-0000-0000-0000-0000000000{:02d}"


def rec(kind, t, uid, **fields):
    """One record in Claude Code's shape: type, timestamp, uuid, sessionId, cwd, plus fields."""
    return {"type": kind, "timestamp": t, "uuid": uid, "sessionId": fields.pop("sid", SID.format(1)),
            "cwd": fields.pop("cwd", "/home/acme/src/acme-api"), **fields}


def human(t, uid, text, **kw):
    return rec("user", t, uid, origin={"kind": "human"}, promptSource="typed",
               message={"role": "user", "content": text}, **kw)


def assistant(t, uid, text, **kw):
    return rec("assistant", t, uid, message={"role": "assistant", "content": [{"type": "text", "text": text}]}, **kw)


def tool_use(t, uid, tid, name, inp, **kw):
    return rec("assistant", t, uid, message={"role": "assistant", "content": [
        {"type": "tool_use", "id": tid, "name": name, "input": inp}]}, **kw)


def tool_result(t, uid, tid, text, error=False, **kw):
    return rec("user", t, uid, message={"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tid, "is_error": error, "content": text}]},
        permissionDecision=kw.pop("permission", {"decision": "accept", "source": "config"}), **kw)


def write(dirpath, name, recs, tail=""):
    path = os.path.join(dirpath, name)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(r) + "\n" for r in recs)
        f.write(tail)
    return path


def run(*argv, stdin=None):
    """Runs main() and returns (exit code, parsed JSON)."""
    out = io.StringIO()
    old_stdin = sys.stdin
    if stdin is not None:
        sys.stdin = io.StringIO(stdin)
    try:
        with contextlib.redirect_stdout(out):
            code = retro_moments.main(list(argv))
    finally:
        sys.stdin = old_stdin
    return code, json.loads(out.getvalue())


class TempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)


if __name__ == "__main__":
    unittest.main()
