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


def kind_fixture(kind):
    return os.path.join(FIXTURES, "kinds", kind + ".jsonl")


class Kinds(TempDir):
    def output(self, *paths, extra=()):
        code, out = run("moments", *paths, *extra)
        self.assertEqual(code, 0)
        return out

    def moments(self, kind):
        return self.output(kind_fixture(kind))["moments"]

    def test_each_kind_yields_exactly_its_moment(self):
        for kind in ["correction", "refusal", "error", "retry", "search", "slow", "stop", "blocked"]:
            with self.subTest(kind=kind):
                m = self.moments(kind)
                self.assertEqual([x["kind"] for x in m], [kind])
                where = m[0]["runs"][0] if kind == "slow" else m[0]  # a slow step cites each of its runs
                self.assertTrue(where["session"] and where["time"] and where["id"])
                self.assertTrue(m[0]["excerpt"])

    def test_only_later_human_messages_are_corrections(self):
        m = self.moments("correction")
        self.assertEqual([(x["kind"], x["id"]) for x in m], [("correction", "c-5")])
        self.assertEqual(m[0]["time"], "2026-03-02T11:14:00Z")
        self.assertIn("date-fns", m[0]["excerpt"])

    def test_a_refusal_says_how_and_which_tool(self):
        m = self.moments("refusal")[0]
        self.assertEqual((m["how"], m["tool"], m["id"]), ("user-rejected", "Bash", "f-3"))

    def test_an_error_quotes_the_command_and_its_first_lines(self):
        m = self.moments("error")[0]
        self.assertEqual(m["tool"], "Bash")
        self.assertTrue(m["excerpt"].startswith("npm test -- usage → FAIL src/usage.test.ts"))

    def test_an_api_error_is_an_error_and_429_is_a_usage_limit(self):
        path = write(self.tmp, "api.jsonl", [
            human("2026-03-02T09:00:00Z", "a-1", "Go"),
            rec("assistant", "2026-03-02T09:01:00Z", "a-2", isApiErrorMessage=True, apiErrorStatus=500,
                message={"role": "assistant", "content": [{"type": "text", "text": "API Error: 500 overloaded"}]}),
            rec("assistant", "2026-03-02T09:02:00Z", "a-3", isApiErrorMessage=True, apiErrorStatus=429,
                message={"role": "assistant", "content": [{"type": "text", "text": "API Error: 429 rate limited"}]}),
            rec("user", "2026-03-02T09:03:00Z", "a-4", usageLimitNote="limit",
                message={"role": "user", "content": "[Usage limit reached]"}),
        ])
        m = self.output(path)["moments"]
        self.assertEqual([(x["kind"], x.get("why"), x["id"]) for x in m],
                         [("error", None, "a-2"), ("blocked", "usage_limit", "a-3"), ("blocked", "usage_limit", "a-4")])

    def test_a_retry_is_reported_once_with_its_count(self):
        m = self.moments("retry")[0]
        self.assertEqual((m["count"], m["tool"], m["excerpt"], m["id"]), (3, "Bash", "npm run lint", "r-u0"))

    def test_the_same_call_further_apart_isnt_a_retry(self):
        recs = [human("2026-03-02T09:00:00Z", "x-1", "Go")]
        cmds = ["npm run lint"] + ["echo %d" % i for i in range(retro_moments.RETRY_WINDOW)] + ["npm run lint"]
        for i, c in enumerate(cmds):
            recs += [tool_use("2026-03-02T09:%02d:00Z" % (i + 1), "u%d" % i, "t%d" % i, "Bash", {"command": c}),
                     tool_result("2026-03-02T09:%02d:01Z" % (i + 1), "r%d" % i, "t%d" % i, "ok")]
        self.assertEqual(self.output(write(self.tmp, "far.jsonl", recs))["moments"], [])

    def test_a_search_counts_its_calls_and_minutes(self):
        m = self.moments("search")[0]
        self.assertEqual((m["count"], m["minutes"], m["id"]), (10, 9.2, "s-u0"))
        self.assertIn("openapi", m["excerpt"])
        self.assertIn("build.ts", m["excerpt"])

    def test_a_question_then_a_human_reply_is_a_stop(self):
        path = write(self.tmp, "ask.jsonl", [
            human("2026-03-02T09:00:00Z", "q-1", "Start"),
            assistant("2026-03-02T09:01:00Z", "q-2", "Should I seed the qa tenant?"),
            human("2026-03-02T09:21:00Z", "q-3", "yes"),
        ])
        stops = [x for x in self.output(path)["moments"] if x["kind"] == "stop"]
        self.assertEqual([(x["id"], x["waited_minutes"]) for x in stops], [("q-2", 20.0)])

    def test_a_stop_on_ask_user_question_waits_until_the_answer(self):
        m = self.moments("stop")[0]
        self.assertEqual((m["id"], m["waited_minutes"]), ("p-2", 12.0))
        self.assertIn("shared database", m["excerpt"])

    def test_signing_failures_sign_in_and_config_signing_errors_are_blocked(self):
        self.assertEqual(self.moments("blocked")[0]["why"], "signing")
        config = os.path.join(self.tmp, "config.yml")
        with open(config, "w") as f:
            f.write("vcs:\n  signed_commits: true\n  signing_errors:\n    - \"agent refused operation\"\n")
        path = write(self.tmp, "b.jsonl", [
            human("2026-03-02T09:00:00Z", "b-1", "Go"),
            tool_use("2026-03-02T09:01:00Z", "b-2", "t1", "Bash", {"command": "git commit -S"}),
            tool_result("2026-03-02T09:01:01Z", "b-3", "t1", "error: agent refused operation", error=True),
            tool_use("2026-03-02T09:02:00Z", "b-4", "t2", "Bash", {"command": "gh pr view"}),
            tool_result("2026-03-02T09:02:01Z", "b-5", "t2", "To get started with GitHub CLI, please run:  gh auth login", error=True),
        ])
        m = self.output(path, extra=("--config", config))["moments"]
        self.assertEqual([(x["kind"], x["why"]) for x in m], [("blocked", "signing"), ("blocked", "sign_in")])

    def test_hook_and_delivery_lookalikes_are_listed_not_moments(self):
        out = self.output(kind_fixture("lookalikes"))
        self.assertEqual(out["moments"], [])
        self.assertEqual([x["id"] for x in out["unknown_shapes"]["hook"]], ["l-3", "l-4"])
        self.assertEqual([x["id"] for x in out["unknown_shapes"]["delivery"]], ["l-5"])
        self.assertEqual(out["unknown_shapes"]["delivery"][0]["line"], 5)

    def test_subagent_transcripts_are_counted_not_read(self):
        path = write(self.tmp, SID.format(1) + ".jsonl", [human("2026-03-02T09:00:00Z", "a", "Go")])
        os.makedirs(os.path.join(self.tmp, SID.format(1), "subagents"))
        for name in ("agent-a.jsonl", "agent-b.jsonl"):
            write(os.path.join(self.tmp, SID.format(1), "subagents"), name,
                  [human("2026-03-02T09:00:00Z", "s", "Go"), human("2026-03-02T09:01:00Z", "s2", "not read")])
        out = self.output(path)
        self.assertEqual(out["subagents_not_read"], 2)
        self.assertEqual(out["moments"], [])

    def test_excerpts_are_trimmed_and_collapsed(self):
        long = "no,   use\n\n date-fns " + "x" * 1000
        path = write(self.tmp, "long.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
                                               human("2026-03-02T09:01:00Z", "b", long)])
        excerpt = self.output(path)["moments"][0]["excerpt"]
        self.assertLessEqual(len(excerpt), retro_moments.EXCERPT)
        self.assertTrue(excerpt.startswith("no, use date-fns x"))

    def test_the_session_is_named_by_its_title(self):
        path = write(self.tmp, "named.jsonl", [
            {"type": "custom-title", "customTitle": "acme-api-3f", "sessionId": SID.format(1)},
            human("2026-03-02T09:00:00Z", "a", "Go"), human("2026-03-02T09:01:00Z", "b", "no")])
        out = self.output(path)
        self.assertEqual(out["moments"][0]["session"], "acme-api-3f")
        self.assertEqual(out["sessions"][0]["session"], "acme-api-3f")
        self.assertEqual(out["sessions"][0]["id"], SID.format(1))
        self.assertEqual(out["sessions"][0]["repo"], "acme-api")


if __name__ == "__main__":
    unittest.main()
