#!/usr/bin/env python3
"""Tests skills/release-notes/scripts/production_date.py with no network: a fake
GitHub answers its `gh api` calls from the recorded fixtures in
scripts/fixtures/production-date/, paging and filtering the way GitHub does.

Run: python3 scripts/production-date.test.py
"""
import contextlib
import copy
import io
import datetime
import json
import os
import subprocess
import sys
import unittest
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "release-notes", "scripts", "production_date.py")
FIXTURES = os.path.join(ROOT, "scripts", "fixtures", "production-date")
sys.path.insert(0, os.path.dirname(SCRIPT))

import production_date  # noqa: E402

GhError = production_date.GhError


def load(name):
    with open(os.path.join(FIXTURES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def day(s):
    return datetime.date.fromisoformat(s)


class FakeGitHub:
    """Answers production_date's gh_api(path) calls from a fixture.

    Like GitHub: workflow runs come newest first, 100 a page at most, and a
    search filtered by `created` or `status` returns at most 1,000 of them, with
    the true total_count. Releases come newest-created first, 100 a page.
    `compare` answers from the fixture's commit graph. Anything it doesn't know
    is a 404, as `gh` reports one. `fail` maps a path prefix to an error.
    """

    SEARCH_LIMIT = 1000

    def __init__(self, fixture, fail=None):
        self.fx = fixture
        self.fail = fail or {}
        self.calls = []

    def __call__(self, path):
        self.calls.append(path)
        for prefix, message in self.fail.items():
            if path.startswith(prefix):
                raise GhError(message)
        url = urlsplit(path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        parts = [unquote(part) for part in url.path.split("/")]
        repo = "/".join(parts[1:3])
        if parts[0] != "repos" or repo != self.fx["repo"]:
            raise GhError("gh: Not Found (HTTP 404)")
        rest = parts[3:]
        if not rest:
            return {"full_name": repo, "default_branch": self.fx["default_branch"]}
        if rest[0] == "pulls" and len(rest) == 2:
            return self._pull(int(rest[1]))
        if rest == ["pulls"]:
            return self._pulls(query)
        if rest[:2] == ["actions", "workflows"] and len(rest) == 3:
            if rest[2] not in self.fx["workflows"]:
                raise GhError("gh: Not Found (HTTP 404)")
            return {"path": ".github/workflows/" + rest[2], "state": "active"}
        if rest[:2] == ["actions", "workflows"] and rest[3:] == ["runs"]:
            return self._runs(rest[2], query)
        if rest[:2] == ["actions", "runs"] and rest[3:4] == ["attempts"]:
            return self._attempt(rest[2], int(rest[4]))
        if rest[:3] == ["git", "ref", "tags"]:
            name = "/".join(rest[3:])
            if name not in self.fx["tags"]:
                raise GhError("gh: Not Found (HTTP 404)")
            annotated = self.fx.get("annotated_tags", {})
            if name in annotated:
                return {"ref": "refs/tags/" + name, "object": {"sha": "tagobj-" + name, "type": "tag"}}
            return {"ref": "refs/tags/" + name, "object": {"sha": self.fx["tag_commits"][name], "type": "commit"}}
        if rest[:2] == ["git", "tags"]:
            for name, sha in self.fx.get("annotated_tags", {}).items():
                if rest[2] == "tagobj-" + name:
                    return {"tag": name, "object": {"sha": sha, "type": "commit"}}
            raise GhError("gh: Not Found (HTTP 404)")
        if rest[0] == "compare":
            base, head = "/".join(rest[1:]).split("...")
            return {"status": self._compare(base, head)}
        if rest == ["releases"]:
            return self._page(sorted(self.fx["releases"], key=lambda r: r["created_at"], reverse=True), query)
        raise GhError("gh: Not Found (HTTP 404)")

    def _pull(self, number):
        for p in self.fx["pulls"]:
            if p["number"] == number:
                return p
        raise GhError("gh: Not Found (HTTP 404)")

    def _pulls(self, query):
        owner, branch = query["head"].split(":", 1)
        found = [p for p in self.fx["pulls"]
                 if p["head"]["ref"] == branch and owner == self.fx["repo"].split("/")[0]
                 and (query.get("state") in ("closed", "all"))]
        return self._page(found, query)

    def _runs(self, workflow, query):
        runs = self.fx["workflows"][workflow]
        if "status" in query:
            runs = [r for r in runs if r["conclusion"] == query["status"]]
        if "created" in query:
            lo, _, hi = query["created"].partition("..")
            hi = hi or lo
            runs = [r for r in runs if lo <= r["created_at"][:10] <= hi]
        runs = sorted(runs, key=lambda r: r["created_at"], reverse=True)
        total = len(runs)
        if "status" in query or "created" in query:
            runs = runs[:self.SEARCH_LIMIT]
        page = self._page(runs, query)
        return {"total_count": total, "workflow_runs": page}

    def _attempt(self, run_id, n):
        attempts = self.fx["attempts"].get(run_id, [])
        if not 1 <= n <= len(attempts):
            raise GhError("gh: Not Found (HTTP 404)")
        return dict(attempts[n - 1], run_attempt=n, id=int(run_id))

    def _ancestors(self, sha):
        seen, todo = set(), [sha]
        while todo:
            s = todo.pop()
            if s in seen:
                continue
            seen.add(s)
            todo.extend(self.fx["commits"].get(s, []))
        return seen

    def _compare(self, base, head):
        commits = self.fx["commits"]
        refs = dict(self.fx.get("tag_commits", {}), **self.fx.get("branches", {}))
        base, head = refs.get(base, base), refs.get(head, head)
        if base not in commits or head not in commits:
            raise GhError("gh: Not Found (HTTP 404)")
        if base == head:
            return "identical"
        if base in self._ancestors(head):
            return "ahead"
        if head in self._ancestors(base):
            return "behind"
        return "diverged"

    @staticmethod
    def _page(items, query):
        per_page = min(int(query.get("per_page", 30)), 100)
        page = int(query.get("page", 1))
        return items[(page - 1) * per_page:page * per_page]


def find(fixture, production, prs, today="2026-03-10", fail=None):
    gh = FakeGitHub(fixture, fail)
    result = production_date.find(fixture["repo"], production, prs, day(today), gh)
    json.dumps(result)  # what it prints must be JSON
    return result, gh


class LandingCommits(unittest.TestCase):
    def test_a_pr_merged_into_main_lands_as_itself(self):
        result, _ = find(load("one-epic"), "merge", [812])
        self.assertEqual(result["prs"], [{"pr": 812, "base": "main", "landing_pr": 812,
                                          "landing_sha": "a812", "landed_at": "2026-02-27T15:04:11Z"}])

    def test_a_pr_merged_into_a_stack_branch_lands_with_that_branch(self):
        result, _ = find(load("stacked"), "merge", [45])
        self.assertEqual(result["prs"][0]["landing_pr"], 44)
        self.assertEqual(result["prs"][0]["landing_sha"], "w044")
        self.assertEqual(result["prs"][0]["landed_at"], "2026-03-05T15:30:00Z")

    def test_landing_follows_the_stack_down_more_than_one_branch(self):
        result, _ = find(load("stacked"), "merge", [47])
        self.assertEqual(result["prs"][0]["landing_pr"], 44)

    def test_the_last_change_is_the_last_to_land_not_the_last_merged(self):
        # #45 merged first (March 1) but landed last (March 5, with #44);
        # #43 merged later (March 3) straight into main.
        result, _ = find(load("stacked"), "merge", [45, 43])
        self.assertEqual(result["last_change"], {"pr": 45, "landing_pr": 44, "landing_sha": "w044",
                                                 "landed_at": "2026-03-05T15:30:00Z"})

    def test_a_pr_whose_branch_never_reached_main_holds_the_note(self):
        result, _ = find(load("stacked"), "merge", [43, 46])
        self.assertEqual(result["status"], "held")
        self.assertIsNone(result["date"])
        not_landed = [p for p in result["prs"] if p.get("landed") is False]
        self.assertEqual([p["pr"] for p in not_landed], [46])
        self.assertIn("slice-2", not_landed[0]["reason"])
        self.assertEqual(result["reason"], "#46 merged into `slice-2`, and no PR has brought it onto `main`")

    def test_an_unmerged_pr_hasnt_landed(self):
        result, _ = find(load("stacked"), "merge", [43, 49])
        self.assertEqual(result["status"], "held")
        self.assertIn("isn't merged", [p for p in result["prs"] if p["pr"] == 49][0]["reason"])

    def test_a_branch_name_with_query_characters_is_encoded(self):
        fx = load("stacked")
        for p in fx["pulls"]:
            for side in ("base", "head"):
                if p[side]["ref"] == "slice-1":
                    p[side]["ref"] = "feat/a+b&c"
        result, _ = find(fx, "merge", [45])
        self.assertEqual(result["prs"][0]["landing_pr"], 44)

    def test_a_reused_branch_name_doesnt_land_a_pr(self):
        # slice-2 was reused for #60, merged into main after #46 merged into the old slice-2.
        result, _ = find(load("stacked"), "merge", [46])
        self.assertEqual(result["status"], "held")
        self.assertIs(result["prs"][0]["landed"], False)

    def test_a_stack_branch_rebased_after_the_lower_pr_merged_still_lands(self):
        result, _ = find(load("rebased-stack"), "merge", [81])
        self.assertEqual(result["status"], "dated")
        self.assertEqual((result["prs"][0]["landing_pr"], result["date"]), (80, "2026-03-04"))

    def test_a_pr_opened_from_the_branch_after_the_merge_doesnt_carry_it(self):
        # #60 reuses slice-2 and merges into main, but was opened after #46 merged into slice-2.
        fx = load("stacked")
        next(p for p in fx["pulls"] if p["number"] == 60)["head"]["sha"] = "w046h"
        result, _ = find(fx, "merge", [46])
        self.assertIs(result["prs"][0]["landed"], False)

    def test_every_pr_open_from_the_branch_is_tried_not_only_the_first_to_merge(self):
        # slice-1 had two PRs open when #81 merged into it: #91 into staging, which merged
        # first and never reached main, and #80 into main.
        fx = load("rebased-stack")
        fx["pulls"].append({"number": 91, "state": "closed", "created_at": "2026-03-01T12:00:00Z",
                            "merged_at": "2026-03-02T12:00:00Z", "merge_commit_sha": "w091",
                            "base": {"ref": "staging"}, "head": {"ref": "slice-1", "sha": "w081"}})
        fx["commits"]["w091"] = ["w081"]
        result, _ = find(fx, "merge", [81])
        self.assertEqual((result["status"], result["prs"][0]["landing_pr"]), ("dated", 80))

    def with_staging(self, staging_pr=None, pushed=False):
        """rebased-stack, plus #91 from slice-1 into staging, open when #81 merged into slice-1."""
        fx = load("rebased-stack")
        fx["pulls"].append({"number": 91, "state": "closed", "created_at": "2026-03-01T12:00:00Z",
                            "merged_at": "2026-03-02T12:00:00Z", "merge_commit_sha": "w091",
                            "base": {"ref": "staging"}, "head": {"ref": "slice-1", "sha": "w081"}})
        fx["commits"]["w091"] = ["w081"]
        if staging_pr:
            fx["pulls"].append(staging_pr)
            fx["commits"][staging_pr["merge_commit_sha"]] = ["w091"]
        if pushed:
            fx["commits"]["w099"] = ["w080", "w091"]
            fx["branches"]["main"] = "w099"
        return fx

    def test_the_path_that_reached_main_first_lands_it(self):
        # staging reached main on March 20, through #92; #80 brought slice-1 to main on March 4.
        fx = self.with_staging({"number": 92, "state": "closed", "created_at": "2026-03-02T00:00:00Z",
                                "merged_at": "2026-03-20T09:00:00Z", "merge_commit_sha": "w092",
                                "base": {"ref": "main"}, "head": {"ref": "staging", "sha": "w091"}})
        result, _ = find(fx, "merge", [81])
        self.assertEqual((result["prs"][0]["landing_pr"], result["date"]), (80, "2026-03-04"))

    def test_a_branch_pushed_to_main_doesnt_stop_a_pr_that_landed_it(self):
        result, _ = find(self.with_staging(pushed=True), "merge", [81])
        self.assertEqual((result["status"], result["prs"][0]["landing_pr"]), ("dated", 80))

    def test_a_path_too_deep_doesnt_stop_one_that_lands(self):
        fx = self.with_staging({"number": 92, "state": "closed", "created_at": "2026-03-02T00:00:00Z",
                                "merged_at": "2026-03-03T09:00:00Z", "merge_commit_sha": "w092",
                                "base": {"ref": "release"}, "head": {"ref": "staging", "sha": "w091"}})
        old, production_date.MAX_STACK = production_date.MAX_STACK, 2
        try:
            result, _ = find(fx, "merge", [81])
        finally:
            production_date.MAX_STACK = old
        self.assertEqual((result["status"], result["prs"][0]["landing_pr"]), ("dated", 80))

    def test_a_pr_cut_off_deep_in_one_stack_is_followed_in_full_on_its_own(self):
        # Under #81, #92 is two branches down and hits the limit; asked about directly, it's
        # one branch down, and simply hasn't reached main.
        fx = self.with_staging({"number": 92, "state": "closed", "created_at": "2026-03-02T00:00:00Z",
                                "merged_at": "2026-03-03T09:00:00Z", "merge_commit_sha": "w092",
                                "base": {"ref": "release"}, "head": {"ref": "staging", "sha": "w091"}})
        old, production_date.MAX_STACK = production_date.MAX_STACK, 2
        try:
            result, _ = find(fx, "merge", [81, 91])
        finally:
            production_date.MAX_STACK = old
        self.assertEqual(result["status"], "held")
        self.assertIs(result["prs"][1]["landed"], False)

    def test_a_crash_keeps_the_prs_found_before_it(self):
        fx = load("one-epic")
        del fx["pulls"][1]["base"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            production_date.main(["--repo", "acme/acme-api", "--merge", "812", "820"], gh=FakeGitHub(fx))
        self.assertEqual([p["pr"] for p in json.loads(out.getvalue())["prs"]], [812])

    def test_a_branch_that_reached_main_without_a_pr_isnt_held_forever(self):
        result, _ = find(load("stacked"), "merge", [50])
        self.assertEqual(result["status"], "not_found")
        self.assertIn("#50", result["reason"])
        self.assertIn("`slice-5` reached `main`, but not through a PR", result["reason"])

    def test_a_crash_isnt_hidden_as_date_not_found(self):
        fx = load("one-epic")
        del fx["pulls"][0]["base"]
        with self.assertRaises(KeyError):
            find(fx, "merge", [812])

    def test_a_crash_still_prints_json_and_fails(self):
        fx = load("one-epic")
        del fx["pulls"][0]["base"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = production_date.main(["--repo", "acme/acme-api", "--merge", "812"], gh=FakeGitHub(fx))
        self.assertEqual(code, 1)
        result = json.loads(out.getvalue())
        self.assertEqual(result["status"], "not_found")
        self.assertIn("KeyError", result["reason"])
        self.assertIn("production_date.py failed", result["reason"])

    def test_a_crash_keeps_what_was_found_before_it(self):
        fx = load("one-epic")
        del fx["workflows"]["deploy-production.yml"][2]["run_attempt"]
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = production_date.main(["--repo", "acme/acme-api", "--workflow", "deploy-production.yml", "820"],
                                        gh=FakeGitHub(fx))
        result = json.loads(out.getvalue())
        self.assertEqual((code, result["status"]), (1, "not_found"))
        self.assertEqual(result["last_change"]["pr"], 820)
        self.assertEqual([p["pr"] for p in result["prs"]], [820])

    def test_squash_merged_stack_more_than_one_branch_deep_lands(self):
        # #70 into slice-2, #71 slice-2 into slice-1, #72 slice-1 into main, all squashed.
        result, _ = find(load("squash-stack"), "merge", [70])
        self.assertEqual(result["status"], "dated")
        self.assertEqual((result["prs"][0]["landing_pr"], result["prs"][0]["landing_sha"]), (72, "w072"))

    def test_a_pr_gh_cant_read_means_date_not_found(self):
        result, _ = find(load("one-epic"), "merge", [812], fail={"repos/acme/acme-api/pulls/812": "gh: HTTP 502"})
        self.assertEqual(result["status"], "not_found")
        self.assertIsNone(result["date"])
        self.assertIn("HTTP 502", result["reason"])


class Merge(unittest.TestCase):
    def test_merge_is_dated_by_the_landing_prs_merge(self):
        result, _ = find(load("one-epic"), "merge", [812, 820])
        self.assertEqual(result["status"], "dated")
        self.assertEqual((result["date"], result["time"]), ("2026-03-02", "2026-03-02T16:20:45Z"))
        self.assertEqual(result["deploy"], {"kind": "merge", "pr": 820, "merged_at": "2026-03-02T16:20:45Z"})

    def test_a_stacked_pr_on_merge_is_dated_by_the_pr_that_landed_it(self):
        result, _ = find(load("stacked"), "merge", [45])
        self.assertEqual(result["date"], "2026-03-05")
        self.assertEqual(result["deploy"]["pr"], 44)


class MissingProduction(unittest.TestCase):
    def test_no_production_means_date_not_found_with_the_evidence(self):
        result, gh = find(load("one-epic"), None, [812, 820])
        self.assertEqual(result["status"], "not_found")
        self.assertIsNone(result["date"])
        self.assertIn("acme/acme-api has no `production` in the config", result["reason"])
        self.assertEqual(result["last_change"]["pr"], 820)
        self.assertIsNone(result["deploy"])
        self.assertFalse([c for c in gh.calls if "/actions/" in c or "/releases" in c])

    def test_no_production_and_a_pr_not_on_main_says_both(self):
        result, _ = find(load("stacked"), None, [43, 46])
        self.assertEqual(result["status"], "not_found")
        self.assertIn("no `production`", result["reason"])
        self.assertIn("#46", result["reason"])


DEPLOY = {"workflow": "deploy-production.yml"}


def run(run_id, sha, created, branch="main", event="push", conclusion="success", attempts=None):
    """A workflow run as gh api returns it, and its attempts."""
    attempts = attempts or [{"conclusion": conclusion, "updated_at": created[:11] + "23:59:00Z"}]
    return ({"id": run_id, "head_sha": sha, "head_branch": branch, "event": event, "status": "completed",
             "conclusion": conclusion, "created_at": created, "run_attempt": len(attempts),
             "html_url": f"https://github.com/acme/acme-api/actions/runs/{run_id}"},
            attempts)


def with_runs(fixture, *runs, replace=False):
    fx = copy.deepcopy(fixture)
    workflow = fx["workflows"]["deploy-production.yml"]
    if replace:
        workflow.clear()
        fx["attempts"].clear()
    for r, attempts in runs:
        workflow.append(r)
        fx["attempts"][str(r["id"])] = attempts
    return fx


def hourly(count, start, sha_for, first_id=10000):
    """`count` successful deploys on main, one an hour from `start`; sha_for(i) is the i-th's commit."""
    t0 = datetime.datetime.fromisoformat(start.replace("Z", "+00:00"))
    runs = []
    for i in range(count):
        created = (t0 + datetime.timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
        finished = (t0 + datetime.timedelta(hours=i, minutes=9)).strftime("%Y-%m-%dT%H:%M:%SZ")
        runs.append(run(first_id + i, sha_for(i), created, attempts=[{"conclusion": "success", "updated_at": finished}]))
    return runs


class Workflow(unittest.TestCase):
    def test_the_first_deploy_containing_the_last_change_dates_it(self):
        result, _ = find(load("one-epic"), DEPLOY, [812, 820])
        self.assertEqual(result["status"], "dated")
        self.assertEqual((result["date"], result["time"]), ("2026-03-03", "2026-03-03T10:12:40Z"))
        self.assertEqual(result["deploy"], {
            "kind": "workflow", "workflow": "deploy-production.yml", "run_id": 3003,
            "url": "https://github.com/acme/acme-api/actions/runs/3003", "head_sha": "a821",
            "head_branch": "main", "event": "push", "attempt": 1, "matched": "compare a820...a821: ahead"})

    def test_an_earlier_deploy_is_found_for_an_earlier_change(self):
        result, _ = find(load("one-epic"), DEPLOY, [812])
        self.assertEqual((result["deploy"]["run_id"], result["time"]), (3001, "2026-02-28T09:11:40Z"))

    def test_a_deploy_of_exactly_the_landing_commit_is_identical(self):
        fx = with_runs(load("one-epic"), run(3010, "a820", "2026-03-02T19:00:00Z"))
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3010)
        self.assertEqual(result["deploy"]["matched"], "compare a820...a820: identical")

    def test_failed_cancelled_pull_request_and_other_branch_runs_dont_count(self):
        fx = with_runs(load("one-epic"),
                       run(3010, "a820", "2026-03-02T17:00:00Z", conclusion="cancelled"),
                       run(3011, "a821", "2026-03-02T17:30:00Z", branch="proj-2403-backend", event="pull_request"),
                       run(3012, "a821", "2026-03-02T18:00:00Z", branch="staging"),
                       run(3013, "a821", "2026-03-02T18:30:00Z", conclusion="failure"))
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3003)

    def test_a_deploy_from_a_tag_counts(self):
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-02T20:00:00Z", branch="v3.21.0"))
        fx["tags"], fx["tag_commits"] = ["v3.21.0"], {"v3.21.0": "a821"}
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3010)
        self.assertEqual(result["deploy"]["head_branch"], "v3.21.0")

    def test_a_deploy_from_an_annotated_tag_counts(self):
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-02T20:00:00Z", branch="v3.21.0"))
        fx["tags"], fx["annotated_tags"] = ["v3.21.0"], {"v3.21.0": "a821"}
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3010)

    def test_a_branch_named_like_a_tag_isnt_a_tag_deploy(self):
        # A branch v3.21.0 at a821, beside a tag v3.21.0 at an older commit.
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-02T20:00:00Z", branch="v3.21.0"))
        fx["tags"], fx["tag_commits"] = ["v3.21.0"], {"v3.21.0": "a812"}
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3003)

    def test_a_branch_name_with_url_characters_isnt_read_as_another_tag(self):
        # Unencoded, `hotfix?x` would ask about the tag `hotfix`.
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-02T20:00:00Z", branch="hotfix?x"))
        fx["tags"], fx["tag_commits"] = ["hotfix"], {"hotfix": "a821"}
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3003)

    def test_a_run_with_no_branch_isnt_a_deploy(self):
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-02T20:00:00Z", branch=None,
                                             event="workflow_dispatch"))
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["deploy"]["run_id"], 3003)

    def test_a_rerun_that_finished_after_a_later_run_doesnt_date_it(self):
        # 3010 started first but succeeded only on a re-run, the next day; 3011 finished first.
        fx = with_runs(load("one-epic"),
                       run(3010, "a821", "2026-03-02T17:00:00Z", attempts=[
                           {"conclusion": "failure", "updated_at": "2026-03-02T17:10:00Z"},
                           {"conclusion": "success", "updated_at": "2026-03-04T08:15:00Z"}]),
                       run(3011, "a821", "2026-03-02T19:00:00Z", attempts=[
                           {"conclusion": "success", "updated_at": "2026-03-02T19:10:00Z"}]))
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual((result["deploy"]["run_id"], result["time"]), (3011, "2026-03-02T19:10:00Z"))

    def test_exactly_a_searchs_worth_of_runs_is_read_not_a_page_limit(self):
        t0 = datetime.datetime(2026, 3, 3, tzinfo=datetime.timezone.utc)
        runs = [run(20000 + i, "a821", (t0 + datetime.timedelta(seconds=60 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
                for i in range(1000)]
        fx = with_runs(load("one-epic"), *runs, replace=True)
        fx["pulls"][1]["merged_at"] = "2026-03-04T00:00:00Z"
        result, _ = find(fx, DEPLOY, [820], today="2026-03-03")
        self.assertEqual((result["status"], result["deploy"]["run_id"]), ("dated", 20000))

    def test_a_deploy_that_succeeded_on_a_rerun_is_dated_by_that_attempt(self):
        fx = with_runs(load("one-epic"), run(3003, "a821", "2026-03-03T23:50:00Z", attempts=[
            {"conclusion": "failure", "updated_at": "2026-03-03T23:58:00Z"},
            {"conclusion": "success", "updated_at": "2026-03-04T08:15:00Z"}]), replace=True)
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual((result["date"], result["deploy"]["attempt"]), ("2026-03-04", 2))

    def test_a_busy_workflow_is_read_past_the_first_page(self):
        # 250 deploys from the day before #812 landed; the first 30 don't contain it.
        runs = hourly(250, "2026-02-26T00:00:00Z", lambda i: "a000" if i < 30 else "a813")
        result, gh = find(with_runs(load("one-epic"), *runs, replace=True), DEPLOY, [812], today="2026-03-12")
        self.assertEqual(result["deploy"]["run_id"], 10030)
        self.assertEqual(result["time"], "2026-02-27T06:09:00Z")
        self.assertTrue(any("page=3" in c for c in gh.calls))

    def test_more_runs_than_a_search_returns_narrows_the_window(self):
        # 1,500 deploys in the window; the first that contains #820 is the 1,100th.
        runs = hourly(1500, "2026-03-01T00:00:00Z", lambda i: "a813" if i < 1100 else "a821")
        result, _ = find(with_runs(load("one-epic"), *runs, replace=True), DEPLOY, [820], today="2026-05-01")
        self.assertEqual(result["status"], "dated")
        self.assertEqual(result["deploy"]["run_id"], 11100)

    def test_one_day_over_the_search_limit_is_not_a_guess(self):
        t0 = datetime.datetime(2026, 3, 3, tzinfo=datetime.timezone.utc)
        runs = [run(20000 + i, "a821", (t0 + datetime.timedelta(seconds=60 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"))
                for i in range(1100)]
        result, _ = find(with_runs(load("one-epic"), *runs, replace=True), DEPLOY, [820])
        self.assertEqual(result["status"], "not_found")
        self.assertIn("page limit", result["reason"])
        self.assertIn("2026-03-03", result["reason"])

    def test_not_deployed_yet_holds_the_note(self):
        fx = load("one-epic")
        fx["workflows"]["deploy-production.yml"] = fx["workflows"]["deploy-production.yml"][:2]
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["status"], "held")
        self.assertIsNone(result["date"])
        self.assertIn("#820", result["reason"])
        self.assertIn("2026-03-10", result["reason"])

    def test_a_workflow_that_has_never_deployed_means_date_not_found(self):
        fx = with_runs(load("one-epic"), run(3010, "a821", "2026-03-03T10:00:00Z", conclusion="failure"),
                       replace=True)
        result, _ = find(fx, DEPLOY, [820])
        self.assertEqual(result["status"], "not_found")
        self.assertIn("no successful `deploy-production.yml` runs", result["reason"])

    def test_a_missing_workflow_file_means_date_not_found(self):
        result, _ = find(load("one-epic"), {"workflow": "deploy-prod.yml"}, [820])
        self.assertEqual(result["status"], "not_found")
        self.assertIn("deploy-prod.yml", result["reason"])

    def test_runs_gh_cant_list_mean_date_not_found_not_a_nearby_date(self):
        result, _ = find(load("one-epic"), DEPLOY, [820],
                         fail={"repos/acme/acme-api/actions/workflows/deploy-production.yml/runs": "gh: HTTP 403"})
        self.assertEqual((result["status"], result["date"]), ("not_found", None))
        self.assertIn("HTTP 403", result["reason"])

    def test_attempts_gh_cant_read_mean_date_not_found(self):
        result, _ = find(load("one-epic"), DEPLOY, [820], fail={"repos/acme/acme-api/actions/runs/3003/attempts": "gh: HTTP 500"})
        self.assertEqual((result["status"], result["date"]), ("not_found", None))
        self.assertIn("HTTP 500", result["reason"])


class Release(unittest.TestCase):
    def test_the_first_published_release_containing_it_dates_it(self):
        result, _ = find(load("release"), "release", [812, 820])
        self.assertEqual(result["status"], "dated")
        self.assertEqual((result["date"], result["time"]), ("2026-03-03", "2026-03-03T09:30:00Z"))
        self.assertEqual(result["deploy"], {
            "kind": "release", "tag": "v3.21.0", "url": "https://github.com/acme/acme-api/releases/tag/v3.21.0",
            "published_at": "2026-03-03T09:30:00Z", "matched": "compare a820...v3.21.0: ahead"})

    def test_drafts_and_prereleases_dont_count(self):
        result, gh = find(load("release"), "release", [820])
        self.assertEqual(result["deploy"]["tag"], "v3.21.0")
        self.assertFalse([c for c in gh.calls if "-draft" in c or "-rc." in c])

    def test_releases_before_the_day_before_it_landed_arent_checked(self):
        fx = load("release")
        fx["releases"].append({"tag_name": "v3.19.0", "draft": False, "prerelease": False,
                               "created_at": "2026-02-28T23:00:00Z", "published_at": "2026-02-28T23:59:00Z",
                               "html_url": "https://github.com/acme/acme-api/releases/tag/v3.19.0"})
        fx["tag_commits"]["v3.19.0"] = "a812"
        _, gh = find(fx, "release", [820])
        self.assertFalse([c for c in gh.calls if c.endswith("...v3.19.0")])
        self.assertTrue([c for c in gh.calls if c.endswith("...v3.20.0")])

    def test_releases_are_checked_by_publish_date_past_the_first_page(self):
        # 150 releases created after #820 landed, all containing it; an older release,
        # created first (so on the last page), was published before them all.
        fx = load("release")
        for i in range(150):
            stamp = (datetime.datetime(2026, 3, 4, tzinfo=datetime.timezone.utc)
                     + datetime.timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            fx["releases"].append({"tag_name": f"v4.{i}.0", "draft": False, "prerelease": False, "created_at": stamp,
                                   "published_at": stamp, "html_url": f"https://github.com/acme/acme-api/releases/tag/v4.{i}.0"})
            fx["tag_commits"][f"v4.{i}.0"] = "a822"
        fx["releases"] = [r for r in fx["releases"] if r["tag_name"] not in ("v3.21.0", "v3.22.0")]
        fx["releases"].append({"tag_name": "v3.21.1", "draft": False, "prerelease": False,
                               "created_at": "2026-02-20T00:00:00Z", "published_at": "2026-03-03T20:00:00Z",
                               "html_url": "https://github.com/acme/acme-api/releases/tag/v3.21.1"})
        fx["tag_commits"]["v3.21.1"] = "a821"
        result, gh = find(fx, "release", [820])
        self.assertEqual((result["deploy"]["tag"], result["time"]), ("v3.21.1", "2026-03-03T20:00:00Z"))
        self.assertTrue(any("releases?" in c and "page=2" in c for c in gh.calls))

    def test_a_tag_name_with_url_characters_is_compared_whole(self):
        fx = load("release")
        for r in fx["releases"]:
            if r["tag_name"] == "v3.21.0":
                r["tag_name"] = "v3.21.0#2"
        fx["tag_commits"]["v3.21.0#2"] = fx["tag_commits"].pop("v3.21.0")
        result, _ = find(fx, "release", [820])
        self.assertEqual(result["deploy"]["tag"], "v3.21.0#2")

    def test_not_released_yet_holds_the_note(self):
        fx = load("release")
        fx["releases"] = fx["releases"][:3]
        result, _ = find(fx, "release", [820])
        self.assertEqual((result["status"], result["date"]), ("held", None))
        self.assertIn("#820", result["reason"])

    def test_releases_gh_cant_read_mean_date_not_found(self):
        result, _ = find(load("release"), "release", [820], fail={"repos/acme/acme-api/releases": "gh: HTTP 401"})
        self.assertEqual((result["status"], result["date"]), ("not_found", None))
        self.assertIn("HTTP 401", result["reason"])


class CommandLine(unittest.TestCase):
    def run_script(self, *args):
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)

    def test_production_options_are_exclusive(self):
        out = self.run_script("--repo", "acme/acme-api", "--merge", "--release", "812")
        self.assertEqual(out.returncode, 2)

    def test_a_pr_number_is_required(self):
        self.assertEqual(self.run_script("--repo", "acme/acme-api", "--merge").returncode, 2)

    def test_a_repo_must_be_owner_slash_name(self):
        self.assertEqual(self.run_script("--repo", "acme-api", "--merge", "812").returncode, 2)


if __name__ == "__main__":
    unittest.main()
