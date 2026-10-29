#!/usr/bin/env python3
"""Tests skills/retro/scripts/retro_moments.py with synthetic transcripts only:
the fixtures in scripts/fixtures/retro-moments/ and transcripts built here. No real
transcript is ever committed.

Run: python3 scripts/retro-moments.test.py
"""
import contextlib
import datetime
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
        self.assertEqual(out["unknown_shapes"]["delivery"][0]["line"], 5)  # not line 8's mid-line mentions

    def test_subagent_transcripts_are_counted_not_read(self):
        path = write(self.tmp, SID.format(1) + ".jsonl", [human("2026-03-02T09:00:00Z", "a", "Go")])
        os.makedirs(os.path.join(self.tmp, SID.format(1), "subagents"))
        for name in ("agent-a.jsonl", "agent-b.jsonl"):
            write(os.path.join(self.tmp, SID.format(1), "subagents"), name,
                  [human("2026-03-02T09:00:00Z", "s", "Go"), human("2026-03-02T09:01:00Z", "s2", "not read")])
        out = self.output(path)
        self.assertEqual(out["subagents_not_read"], 2)
        self.assertEqual(out["moments"], [])

    def test_a_record_without_a_timestamp_or_with_a_naive_one_doesnt_stop_the_run(self):
        recs = [human("2026-03-02T09:00:00Z", "a", "Go"), human("2026-03-02T09:01:00", "b", "naive time"),
                tool_use(None, "c", "t1", "Bash", {"command": "npm test"}),
                tool_result("2026-03-02T09:03:00Z", "d", "t1", "FAIL", error=True),
                human(None, "e", "no time")]
        code, out = run("moments", write(self.tmp, "t.jsonl", recs))
        self.assertEqual(code, 0)
        self.assertEqual(sorted(m["id"] for m in out["moments"]), ["b", "d", "e"])

    def test_signing_text_in_a_successful_result_isnt_blocked(self):
        path = write(self.tmp, "s.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            tool_use("2026-03-02T09:01:00Z", "b", "t1", "Read", {"file_path": "/home/acme/src/acme-api/notes.md"}),
            tool_result("2026-03-02T09:01:01Z", "c", "t1", "matches gpg failed to sign and gh auth login")])
        self.assertEqual(self.output(path)["moments"], [])

    def searches(self, middle):
        recs = [human("2026-03-02T09:00:00Z", "a", "Find it")]
        for i in range(5):
            recs += [tool_use("2026-03-02T09:%02d:00Z" % (i + 1), "u%d" % i, "t%d" % i, "Grep", {"pattern": "p%d" % i}),
                     tool_result("2026-03-02T09:%02d:01Z" % (i + 1), "r%d" % i, "t%d" % i, "…")]
        recs += middle
        for i in range(5, 10):
            recs += [tool_use("2026-03-02T09:%02d:00Z" % (i + 11), "u%d" % i, "t%d" % i, "Grep", {"pattern": "p%d" % i}),
                     tool_result("2026-03-02T09:%02d:01Z" % (i + 11), "r%d" % i, "t%d" % i, "…")]
        return [m for m in self.output(write(self.tmp, "g.jsonl", recs))["moments"] if m["kind"] == "search"]

    def test_a_new_human_message_ends_a_search(self):
        self.assertEqual(self.searches([human("2026-03-02T09:10:00Z", "h", "keep going")]), [])

    def test_a_tool_that_isnt_an_edit_doesnt_end_a_search(self):
        middle = [tool_use("2026-03-02T09:10:00Z", "x", "tx", "TodoWrite", {"todos": []}),
                  tool_result("2026-03-02T09:10:01Z", "y", "tx", "ok")]
        self.assertEqual([m["count"] for m in self.searches(middle)], [10])

    def test_a_bash_write_isnt_a_search(self):
        middle = [tool_use("2026-03-02T09:10:00Z", "x", "tx", "Bash", {"command": "cat > notes.md <<'EOF'\nx\nEOF"}),
                  tool_result("2026-03-02T09:10:01Z", "y", "tx", "")]
        self.assertEqual([m["count"] for m in self.searches(middle)], [10])  # 11 if the write counted
        self.assertFalse(retro_moments.READ_ONLY_BASH.match("grep -c x a.txt > out.txt"))
        self.assertTrue(retro_moments.READ_ONLY_BASH.match("grep -rn x src 2>&1 | head"))
        for quoted in ("grep -rn '=> ' src", 'rg "a -> b" lib', "grep -c '>=' x.ts"):
            self.assertTrue(retro_moments.READ_ONLY_BASH.match(quoted), quoted)

    def test_a_refusal_with_two_results_is_reported_once(self):
        r = rec("user", "2026-03-02T09:01:01Z", "f", toolDenialKind="automode-blocked", message={"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "is_error": True, "content": "denied"},
            {"type": "tool_result", "tool_use_id": "t2", "is_error": True, "content": "denied"}]})
        path = write(self.tmp, "r.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            rec("assistant", "2026-03-02T09:01:00Z", "b", message={"role": "assistant", "content": [
                {"type": "tool_use", "id": "t1", "name": "Bash", "input": {"command": "rm -rf build"}},
                {"type": "tool_use", "id": "t2", "name": "Bash", "input": {"command": "rm -rf dist"}}]}), r])
        self.assertEqual([m["kind"] for m in self.output(path)["moments"]], ["refusal"])

    def test_a_tool_input_that_isnt_an_object_doesnt_stop_the_run(self):
        path = write(self.tmp, "i.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            tool_use("2026-03-02T09:01:00Z", "b", "t1", "Bash", "ls"),
            tool_result("2026-03-02T09:01:01Z", "c", "t1", "boom", error=True)])
        code, out = run("moments", path)
        self.assertEqual((code, [m["kind"] for m in out["moments"]]), (0, ["error"]))

    def test_an_interruption_without_an_origin_counts(self):
        path = write(self.tmp, "i.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            rec("user", "2026-03-02T09:01:00Z", "b", message={"role": "user", "content": "[Request interrupted by user]"})])
        self.assertEqual([(m["kind"], m["id"]) for m in self.output(path)["moments"]], [("correction", "b")])

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


def seed_session(tmp, n, runs, extra=()):
    """A session in acme-api that runs the seed `runs` times: [(start, minutes, cd-prefixed?)]."""
    sid = SID.format(n)
    recs = [human("2026-03-0%dT08:00:00Z" % n, "h%d" % n, "Seed it", sid=sid)]
    for i, (start, minutes, cd) in enumerate(runs):
        end = (retro_moments.parse_time(start) + datetime.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
        cmd = ("cd /home/acme/src/acme-api && " if cd else "") + "npm run seed -- --tenant qa"
        recs += [tool_use(start, "s%d-u%d" % (n, i), "s%d-t%d" % (n, i), "Bash", {"command": cmd}, sid=sid),
                 tool_result(end, "s%d-r%d" % (n, i), "s%d-t%d" % (n, i), "Seeding…\nSeeded tenant qa: 2,104,332 usage rows", sid=sid)]
    return write(tmp, sid + ".jsonl", recs + list(extra))


def two_sessions_with_seed_runs(tmp):
    """5 seed runs (19.4 + 20.1 + 19.8 + 21.0 + 20.3 = 100.6 minutes) over two sessions, plus calls that
    took long only because they waited: one the user approved, one in the background, an AskUserQuestion,
    and one with no result yet."""
    sid = SID.format(1)
    waits = [
        tool_use("2026-03-01T13:00:00Z", "w-u1", "w-t1", "Bash", {"command": "npm run migrate"}, sid=sid),
        tool_result("2026-03-01T13:10:00Z", "w-r1", "w-t1", "done", sid=sid,
                    permission={"decision": "accept", "source": "user_temporary"}),
        tool_use("2026-03-01T14:00:00Z", "w-u2", "w-t2", "Bash", {"command": "npm run dev", "run_in_background": True}, sid=sid),
        tool_result("2026-03-01T14:10:00Z", "w-r2", "w-t2", "started", sid=sid),
        tool_use("2026-03-01T15:00:00Z", "w-u3", "w-t3", "AskUserQuestion", {"questions": [{"question": "Which tenant?"}]}, sid=sid),
        tool_result("2026-03-01T15:06:40Z", "w-r3", "w-t3", "qa", sid=sid),
        tool_use("2026-03-01T16:00:00Z", "w-u4", "w-t4", "Bash", {"command": "npm run e2e"}, sid=sid),
    ]
    first = seed_session(tmp, 1, [("2026-03-01T09:05:00Z", 19.4, True), ("2026-03-01T16:10:00Z", 20.1, False)], waits)
    second = seed_session(tmp, 2, [("2026-03-02T09:02:00Z", 19.8, False), ("2026-03-02T14:30:00Z", 21.0, True),
                                   ("2026-03-02T16:01:00Z", 20.3, False)])
    return [first, second]


class Slow(TempDir):
    def slow(self, *paths, extra=()):
        code, out = run("moments", *paths, *extra)
        self.assertEqual(code, 0)
        return [m for m in out["moments"] if m["kind"] == "slow"]

    def test_a_command_run_five_times_is_one_slow_moment(self):
        slow = self.slow(*two_sessions_with_seed_runs(self.tmp))
        self.assertEqual(len(slow), 1)
        self.assertEqual((slow[0]["command"], slow[0]["repo"], slow[0]["count"]), ("npm run seed -- --tenant qa", "acme-api", 5))
        self.assertAlmostEqual(slow[0]["total_minutes"], 100.6, places=1)
        self.assertEqual([r["minutes"] for r in slow[0]["runs"]], [19.4, 20.1, 19.8, 21.0, 20.3])
        self.assertEqual({r["session"] for r in slow[0]["runs"]}, {SID.format(1)[:8], SID.format(2)[:8]})
        self.assertEqual(slow[0]["excerpt"], "Seeded tenant qa: 2,104,332 usage rows")

    def test_a_call_the_user_approved_isnt_slow(self):
        commands = [m["command"] for m in self.slow(*two_sessions_with_seed_runs(self.tmp))]
        for waited in ("npm run migrate", "npm run dev", "npm run e2e", "Which tenant?"):
            self.assertNotIn(waited, commands)

    def test_the_same_command_in_two_folders_is_two_slow_steps(self):
        recs = [human("2026-03-02T09:00:00Z", "h", "Build")]
        for i, folder in enumerate(["frontend", "backend", "frontend"]):
            recs += [tool_use("2026-03-02T1%d:00:00Z" % i, "u%d" % i, "t%d" % i, "Bash", {"command": "cd %s && npm run build" % folder}),
                     tool_result("2026-03-02T1%d:05:00Z" % i, "r%d" % i, "t%d" % i, "built")]
        slow = self.slow(write(self.tmp, "mono.jsonl", recs))
        self.assertEqual(sorted((m["command"], m["count"]) for m in slow),
                         [("cd backend && npm run build", 1), ("cd frontend && npm run build", 2)])

    def test_cd_folders_are_normalised_before_grouping(self):
        recs = [human("2026-03-02T09:00:00Z", "h", "Build")]
        cds = ["cd ./frontend", "cd frontend", "cd frontend/", 'cd "frontend"', "cd /home/acme/src/acme-api/frontend"]
        for i, cd in enumerate(cds):
            recs += [tool_use("2026-03-02T1%d:00:00Z" % i, "u%d" % i, "t%d" % i, "Bash", {"command": cd + " && npm run build"}),
                     tool_result("2026-03-02T1%d:05:00Z" % i, "r%d" % i, "t%d" % i, "built")]
        slow = self.slow(write(self.tmp, "cds.jsonl", recs))
        self.assertEqual([(m["command"], m["count"]) for m in slow], [("cd frontend && npm run build", 5)])
        self.assertEqual(retro_moments.normalise("cd ~/src/acme-api && npm test", "~/src/acme-api"), "npm test")

    def test_the_repo_comes_from_repo_of(self):
        paths = two_sessions_with_seed_runs(self.tmp)
        slow = self.slow(*paths, extra=("--repo-of", "/home/acme/src/acme-api=api"))
        self.assertEqual(slow[0]["repo"], "api")

    def test_a_long_turn_is_slow_and_a_gap_between_turns_isnt(self):
        path = write(self.tmp, "turns.jsonl", [
            human("2026-03-02T09:00:00Z", "t-1", "Build it"),
            rec("system", "2026-03-02T09:40:00Z", "t-2", subtype="turn_duration", durationMs=31 * 60 * 1000),
            rec("system", "2026-03-02T09:41:00Z", "t-3", subtype="turn_duration", durationMs=29 * 60 * 1000),
            human("2026-03-02T13:00:00Z", "t-4", "Next slice please"),
            rec("system", "2026-03-02T13:05:00Z", "t-5", subtype="turn_duration", durationMs=5 * 60 * 1000),
        ])
        slow = self.slow(path)
        self.assertEqual([(m["kind_of"], m["command"], m["total_minutes"], m["runs"][0]["id"]) for m in slow],
                         [("turn", None, 31.0, "t-2")])


class Totals(TempDir):
    def test_totals_per_session(self):
        sid = SID.format(1)
        path = write(self.tmp, "t.jsonl", [
            human("2026-03-02T09:00:00Z", "a", "Go"),
            rec("user", "2026-03-02T09:01:00Z", "b", origin={"kind": "peer", "msg_id": "m"},
                message={"role": "user", "content": "run-slice: next"}),
            rec("user", "2026-03-02T09:02:00Z", "c", origin={"kind": "task-notification"},
                message={"role": "user", "content": "<task-notification>done</task-notification>"}),
            rec("user", "2026-03-02T09:02:30Z", "m", isMeta=True, message={"role": "user", "content": "<system-reminder>x"}),
            tool_use("2026-03-02T09:03:00Z", "d", "t1", "Bash", {"command": "npm test"}),
            tool_result("2026-03-02T09:03:10Z", "e", "t1", "FAIL", error=True),
            tool_use("2026-03-02T09:04:00Z", "f", "t2", "Read", {"file_path": "/home/acme/src/acme-api/a.ts"}),
            tool_result("2026-03-02T09:04:01Z", "g", "t2", "…"),
            tool_use("2026-03-02T09:05:00Z", "h", "t3", "Bash", {"command": "npm test"}),
            tool_result("2026-03-02T09:05:10Z", "i", "t3", "ok"),
            rec("assistant", "2026-03-02T09:30:00Z", "j", isApiErrorMessage=True, apiErrorStatus=500,
                message={"role": "assistant", "content": [{"type": "text", "text": "API Error: 500"}]}),
        ])
        code, out = run("moments", path)
        self.assertEqual(out["sessions"][0]["id"], sid)
        self.assertEqual(out["sessions"][0]["totals"],
                         {"turns": 3, "tool_calls": {"Bash": 2, "Read": 1}, "errors": 2, "minutes": 30.0})

    def test_a_refusal_isnt_counted_as_an_error(self):
        path = write(self.tmp, "r.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            tool_use("2026-03-02T09:01:00Z", "b", "t1", "Bash", {"command": "rm -rf build"}),
            tool_result("2026-03-02T09:01:01Z", "c", "t1", "denied", error=True, toolDenialKind="user-rejected")])
        code, out = run("moments", path)
        self.assertEqual(out["sessions"][0]["totals"]["errors"], 0)


class Window(TempDir):
    def test_records_outside_the_window_are_left_out(self):
        paths = two_sessions_with_seed_runs(self.tmp)
        code, out = run("moments", *paths, "--since", "2026-03-02T00:00:00Z", "--until", "2026-03-02T15:00:00Z")
        self.assertEqual(out["window"], ["2026-03-02T00:00:00Z", "2026-03-02T15:00:00Z"])
        slow = [m for m in out["moments"] if m["kind"] == "slow"]
        self.assertEqual([r["minutes"] for r in slow[0]["runs"]], [19.8, 21.0])
        self.assertEqual(slow[0]["count"], 2)
        first = out["sessions"][0]["totals"]
        self.assertEqual((first["turns"], first["tool_calls"], first["minutes"]), (0, {}, 0))
        second = out["sessions"][1]["totals"]
        self.assertEqual((second["turns"], second["tool_calls"]), (1, {"Bash": 2}))

    def calls(self, name, inputs):
        recs = [human("2026-03-02T09:00:00Z", "h", "Go")]
        for i, inp in enumerate(inputs):
            recs += [tool_use("2026-03-02T09:%02d:00Z" % (i + 1), "u%d" % i, "t%d" % i, name, inp),
                     tool_result("2026-03-02T09:%02d:01Z" % (i + 1), "r%d" % i, "t%d" % i, "…")]
        return write(self.tmp, "calls.jsonl", recs)

    def kinds(self, path, *window):
        code, out = run("moments", path, *window)
        return [(m["kind"], m.get("count")) for m in out["moments"]]

    def test_retries_count_only_calls_inside_the_window(self):
        path = self.calls("Bash", [{"command": "npm test"}, {"command": "ls"}, {"command": "npm test"},
                                   {"command": "ls -a"}, {"command": "npm test"}])
        self.assertEqual(self.kinds(path, "--until", "2026-03-02T09:02:00Z"), [])
        self.assertEqual(self.kinds(path, "--since", "2026-03-02T09:02:00Z"), [("retry", 2)])

    def test_searches_count_only_calls_inside_the_window(self):
        path = self.calls("Grep", [{"pattern": "p%d" % i} for i in range(12)])
        self.assertEqual(self.kinds(path), [("search", 12)])
        self.assertEqual(self.kinds(path, "--until", "2026-03-02T09:03:00Z"), [])
        self.assertEqual(self.kinds(path, "--since", "2026-03-02T09:02:30Z"), [("search", 10)])

    def test_a_moment_outside_the_window_is_left_out(self):
        code, out = run("moments", kind_fixture("correction"), "--until", "2026-03-02T10:00:00Z")
        self.assertEqual(out["moments"], [])


class Unparseable(unittest.TestCase):
    def setUp(self):
        code, self.out = run("moments", os.path.join(FIXTURES, "broken.jsonl"))
        self.assertEqual(code, 0)

    def test_a_line_that_isnt_json_is_reported_and_the_rest_still_read(self):
        self.assertIn({"session": SID.format(3)[:8], "line": 2, "reason": "not JSON"}, self.out["unparseable"])
        self.assertEqual([(m["kind"], m["id"]) for m in self.out["moments"]], [("correction", "k-5")])

    def test_an_unknown_type_is_counted_not_an_error(self):
        self.assertEqual(self.out["unknown_types"], {"some-new-type": 1})

    def test_an_incomplete_last_line_is_reported(self):
        self.assertIn({"session": SID.format(3)[:8], "line": 6, "reason": "incomplete last line (still being written?)"},
                      self.out["unparseable"])

    def test_a_record_missing_its_message_is_reported(self):
        self.assertIn({"session": SID.format(3)[:8], "line": 4, "reason": "missing message"}, self.out["unparseable"])
        self.assertEqual(len(self.out["unparseable"]), 3)

    def test_a_message_whose_content_isnt_text_or_a_list_is_reported(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp)
        path = write(tmp, "c.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
                                      rec("user", "2026-03-02T09:01:00Z", "b", message={"role": "user", "content": 42}),
                                      human("2026-03-02T09:02:00Z", "c", "no, the other one")])
        code, out = run("moments", path)
        self.assertEqual(code, 0)
        self.assertEqual(out["unparseable"][0]["reason"], "unsupported message content")
        self.assertEqual([m["id"] for m in out["moments"]], ["c"])

    def test_a_missing_transcript_is_reported_and_the_rest_still_read(self):
        missing = "/home/acme/" + SID.format(9) + ".jsonl"
        code, out = run("moments", missing, os.path.join(FIXTURES, "kinds", "correction.jsonl"))
        self.assertEqual(code, 0)
        self.assertEqual([m["id"] for m in out["moments"]], ["c-5"])
        self.assertEqual(out["unparseable"], [])
        self.assertEqual(len(out["unreadable"]), 1)
        self.assertEqual((out["unreadable"][0]["session"], out["unreadable"][0]["path"]), (SID.format(9)[:8], missing))
        self.assertTrue(out["unreadable"][0]["reason"].startswith("can't read the file"))

    def test_fixtures_are_synthetic(self):
        """No real transcript is committed: every fixture record has a made-up session and an Acme cwd."""
        checked = 0
        for folder, _, files in os.walk(FIXTURES):
            for name in files:
                if not name.endswith(".jsonl"):
                    continue
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    for line in f:
                        try:
                            r = json.loads(line)
                        except ValueError:
                            continue
                        if "sessionId" in r:
                            self.assertTrue(r["sessionId"].startswith("00000000-"), (name, r["sessionId"]))
                            checked += 1
                        if "cwd" in r:
                            self.assertTrue(r["cwd"].startswith("/home/acme/"), (name, r["cwd"]))
        self.assertGreater(checked, 20)


PLANTED = ["ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8", "eyJhbGciOiJIUzI1NiJ9", "s3cret", "b3BlbnNzaC1rZXktdjEAAAAABG5vbmU",
           "dana.k@zephyr-corp.com", "zephyr-corp.atlassian.net", "7d3f2a10-5b6c-4e8d-9f01-23456789abcd",
           "api.zephyr-corp.internal", "10.20.30.40", "qa+7@zephyr-corp.com", "zephyr-corp.com", "hunter2",
           "db.zephyr-corp.internal", "Zx8Kq2Lm9Np4Rt7Vw1Yb3Cd6Fg0Hj5Ks8Mn2Pq4St7Uv9Wx1"]
CONFIGS = ("--config", os.path.join(FIXTURES, "redaction-config.yml"),
           "--config", os.path.join(FIXTURES, "redaction-local.yml"))


class Redaction(TempDir):
    def setUp(self):
        super().setUp()
        code, self.out = run("moments", os.path.join(FIXTURES, "redaction.jsonl"), *CONFIGS)
        self.assertEqual(code, 0)
        self.by_id = {m["id"]: m for m in self.out["moments"]}

    def excerpt(self, key):
        return self.by_id["x-" + key]["excerpt"]

    def test_no_planted_value_is_in_the_output(self):
        text = json.dumps(self.out).lower()
        for value in PLANTED:
            with self.subTest(value=value):
                self.assertNotIn(value.lower(), text)

    def test_replacements_say_what_was_there(self):
        self.assertIn("[token]", self.excerpt("token"))
        self.assertIn("Authorization: [redacted]", self.excerpt("auth"))
        self.assertIn("postgres://[redacted]", self.excerpt("conn"))
        self.assertIn("[private key]", self.excerpt("key"))
        self.assertIn("[email]", self.excerpt("email"))
        self.assertIn("[config: jira.site]", self.excerpt("site"))
        self.assertIn("[config: jira.cloud_id]", self.excerpt("cloud"))
        self.assertIn("[config: database.host]", self.excerpt("ip"))

    def test_a_long_unknown_token_drops_the_quote(self):
        for key in ("unknown", "cutkey"):
            with self.subTest(key=key):
                m = self.by_id["x-" + key]
                self.assertEqual((m["excerpt"], m["excerpt_dropped"]), (None, True))
                self.assertEqual(m["time"][:10], "2026-03-02")
        dropped = {d["id"] for d in self.out["redaction"]["dropped"]}
        self.assertEqual(dropped, {"x-unknown", "x-cutkey"})
        self.assertGreaterEqual(self.out["redaction"]["redacted"], 11)

    def test_a_commit_sha_is_kept(self):
        self.assertIn("3f9a1c2e7b4d8f0a6c5e1b9d2f7a3c8e4b6d0f1a", self.excerpt("sha"))
        self.assertFalse(self.by_id["x-sha"].get("excerpt_dropped"))

    def test_ordinary_paths_and_words_are_kept(self):
        for text in ("/home/acme/src/acme-api/scripts/openapi/build.ts", "docs/plans/2026-10-28-issue-92-retro.md",
                     "retro-ranks-and-routes-checks-and-review-rules", "localhost:3000 and http://localhost:8080",
                     "pushed to github"):
            with self.subTest(text=text):
                code, out = run("redact", *CONFIGS, stdin=text)
                self.assertEqual((out["text"], out["dropped"]), (text, False))

    def test_redact_on_stdin_matches_moments(self):
        with open(os.path.join(FIXTURES, "redaction.jsonl")) as f:
            recs = [json.loads(line) for line in f]
        for r in recs[1:]:
            code, out = run("redact", *CONFIGS, stdin=r["message"]["content"])
            moment = self.by_id[r["uuid"]]
            with self.subTest(id=r["uuid"]):
                self.assertEqual(out["dropped"], bool(moment.get("excerpt_dropped")))
                if not out["dropped"]:
                    self.assertEqual(retro_moments.trim(out["text"]), moment["excerpt"])
                else:
                    self.assertIsNone(out["text"])
                    self.assertTrue(out["reason"])

    def redacted(self, text, configs=CONFIGS):
        code, out = run("redact", *configs, stdin=text)
        return out["text"]

    def test_secret_names_inside_env_vars_and_json_are_redacted(self):
        for text in ("PGPASSWORD=s3cr3t-pw psql", "export DB_PASSWORD=s3cr3t-pw", "GITHUB_TOKEN=abc123xyz gh pr",
                     '{"password": "s3cr3t-pw"}', '"apiKey": "Zx9_k2abc"', '"Authorization": "Bearer abcdefgh"',
                     "client_secret: 'abc123xyz'"):
            with self.subTest(text=text):
                out = self.redacted(text)
                for secret in ("s3cr3t-pw", "abc123xyz", "Zx9_k2abc", "abcdefgh"):
                    self.assertNotIn(secret, out or "")
                self.assertIn("[redacted]", out)

    def test_the_password_in_a_config_url_is_private(self):
        self.assertNotIn("hunter2", self.redacted("the password is hunter2"))

    def test_hostnames_anywhere_in_the_config_are_private(self):
        config = os.path.join(self.tmp, "hosts.yml")
        with open(config, "w") as f:
            f.write("stack:\n  frontend_host: app.zephyr-corp.com\n"
                    "  database:\n    local: the shared db at db2.zephyr-corp.internal:5432\n"
                    "  how: >-\n    Start it, then open\n    https://bastion.zephyr-corp.io/login\n"
                    "  note: see config.example.yml\n")
        values = dict(retro_moments.private_values([config]))
        for host in ("app.zephyr-corp.com", "db2.zephyr-corp.internal", "bastion.zephyr-corp.io"):
            self.assertIn(host, values)
        self.assertNotIn("config.example.yml", values)

    def test_hex_keys_and_hyphenated_tokens_drop_the_quote(self):
        for text in ("X-Api-Key 3f9a1c2b4d5e6f708192a3b4c5d6e7f8", "abcd1234efgh5678-ijkl9012mnop3456-qrst7890"):
            with self.subTest(text=text):
                self.assertIsNone(self.redacted(text))

    def test_slashed_and_letter_only_tokens_and_bare_40_hex_drop_the_quote(self):
        for text in ("key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "kQzXwLrTpMvNbYhGfDsAjCeUiOoPlKmJnHbGvFcDxSzAqWeR",
                     "oauth 3f9a1c2b4d5e6f708192a3b4c5d6e7f80a1b2c3d"):
            with self.subTest(text=text):
                self.assertIsNone(self.redacted(text))

    def test_a_quoted_secret_with_spaces_is_redacted_whole(self):
        out = self.redacted('{"password": "correct horse battery"}')
        for word in ("correct", "horse", "battery"):
            self.assertNotIn(word, out)

    def test_two_label_hosts_are_private_and_local_url_users_arent(self):
        config = os.path.join(self.tmp, "two.yml")
        with open(config, "w") as f:
            f.write("deploy:\n  how: deploy from zephyr.io with Next.js\n"
                    "stack:\n  database:\n    url: postgres://postgres:postgres@localhost:5432/app\n"
                    "    shared: postgres://admin:pa55word@db.zephyr.io/app\n"
                    "  secrets_file: .env.test\n  how: run scripts/seed.prod in docs/x.internal\n")
        values = dict(retro_moments.private_values([config]))
        self.assertIn("zephyr.io", values)
        self.assertIn("pa55word", values)
        for word in ("postgres", "admin", "Next.js", "env.test", "seed.prod", "x.internal"):
            self.assertNotIn(word, values)

    def test_a_password_only_url_and_an_escaped_quote_are_redacted(self):
        self.assertNotIn("s3cr3t", self.redacted("connect redis://:s3cr3t@cache.test:6379/0 failed"))
        out = self.redacted('{"password": "correct \\"horse\\" battery"}')
        for word in ("correct", "horse", "battery"):
            self.assertNotIn(word, out)

    def test_private_keys_without_dots_are_private_but_symbolic_hosts_arent(self):
        config = os.path.join(self.tmp, "plain.yml")
        with open(config, "w") as f:
            f.write("vcs:\n  host: github\nstack:\n  database:\n    host: zephyrdb\n  frontend_host: bastion\n")
        values = dict(retro_moments.private_values([config]))
        self.assertIn("zephyrdb", values)
        self.assertIn("bastion", values)
        self.assertNotIn("github", values)

    def test_a_session_title_is_redacted(self):
        path = write(self.tmp, "t.jsonl", [
            {"type": "custom-title", "customTitle": "Fix login for dana.k@zephyr-corp.com", "sessionId": SID.format(1)},
            human("2026-03-02T09:00:00Z", "a", "Go"), human("2026-03-02T09:01:00Z", "b", "no")])
        code, out = run("moments", path, *CONFIGS)
        self.assertNotIn("dana.k", json.dumps(out))
        self.assertEqual(out["sessions"][0]["session"], "Fix login for [email]")
        self.assertEqual(out["moments"][0]["session"], "Fix login for [email]")

    def test_config_values_are_replaced_as_whole_words(self):
        config = os.path.join(self.tmp, "words.yml")
        with open(config, "w") as f:
            f.write("stack:\n  database:\n    host: postgres\n")
        out = self.redacted("run postgres, not postgresql or mypostgres", ("--config", config))
        self.assertEqual(out, "run [config: database.host], not postgresql or mypostgres")

    def test_config_values_next_to_an_underscore_or_a_digit_are_replaced(self):
        config = os.path.join(self.tmp, "words.yml")
        with open(config, "w") as f:
            f.write("stack:\n  database:\n    host: acmedb\n  jira:\n    board_id: 4821\n")
        configs = ("--config", config)
        for text in ("ACMEDB_HOST=x", "acmedb2 is up", "acmedb_replica lags", "use 2acmedb", "board4821"):
            with self.subTest(text=text):
                out = self.redacted(text, configs)
                self.assertNotIn("acmedb", out.lower())
                self.assertNotIn("4821", out)
        for text in ("acmedbx and xacmedb", "48210 and 14821"):
            with self.subTest(text=text):
                self.assertEqual(self.redacted(text, configs), text)

    def test_file_names_ids_and_shas_are_kept(self):
        for text in ("Read src/components/UsageTableReport2024Final.tsx",
                     "session 7d3f2a11-5b6c-4e8d-9f01-23456789abce/subagents",
                     "git show 3f9a1c2e7b4d8f0a6c5e1b9d2f7a3c8e4b6d0f1a", "the tokens = 12",
                     "range 3f9a1c2e7b4d8f0a6c5e1b9d2f7a3c8e4b6d0f1a..main",
                     "ThisIsAVeryLongCamelCaseClassNameForTesting and getUserAccountSettingsFromDatabaseById",
                     "mcp__plugin_playwright_playwright__browser_take_screenshot"):
            with self.subTest(text=text):
                self.assertEqual(self.redacted(text), text)

    def test_a_withheld_command_is_listed_as_dropped(self):
        token = "Zx8Kq2Lm9Np4Rt7Vw1Yb3Cd6Fg0Hj5Ks8Mn2Pq4St7Uv9Wx1"
        path = write(self.tmp, "slow.jsonl", [human("2026-03-02T09:00:00Z", "a", "Go"),
            tool_use("2026-03-02T09:01:00Z", "b", "t1", "Bash", {"command": "curl -s https://x.test/" + token}),
            tool_result("2026-03-02T09:05:00Z", "c", "t1", "ok")])
        code, out = run("moments", path)
        slow = [m for m in out["moments"] if m["kind"] == "slow"][0]
        self.assertEqual(slow["command"], "[withheld]")
        self.assertNotIn(token, json.dumps(out))
        self.assertEqual([d["kind"] for d in out["redaction"]["dropped"]], ["slow"])

    def test_private_values_reads_the_config_shapes(self):
        config = write(self.tmp, "c.yml", [])
        with open(config, "w") as f:
            f.write("tracker:\n  github:\n    repo: zephyr/core  # not private by key\n"
                    "  jira:\n    site: 'zephyr.atlassian.net'\n    board_id: 4821\n    cloud_id: abc\n"
                    "stack:\n  services:\n    - { name: API, url: \"https://api.zephyr.dev:8443/v1\" }\n"
                    "    - { name: web, url: \"http://127.0.0.1:3000\" }\n"
                    "  how: run it on 0.0.0.0 # site: commented.example.com\n"
                    "  note: ask ops@zephyr.dev or 192.168.4.20\n")
        values = dict(retro_moments.private_values([config]))
        self.assertEqual(values.get("zephyr.atlassian.net"), "jira.site")
        self.assertEqual(values.get("4821"), "jira.board_id")
        self.assertIn("https://api.zephyr.dev:8443/v1", values)
        self.assertIn("api.zephyr.dev", values)
        self.assertIn("ops@zephyr.dev", values)
        self.assertIn("192.168.4.20", values)
        for absent in ("abc", "127.0.0.1", "0.0.0.0", "commented.example.com", "zephyr/core", "localhost"):
            self.assertNotIn(absent, values)


if __name__ == "__main__":
    unittest.main()
