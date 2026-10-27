#!/usr/bin/env python3
"""Tests skills/release-notes/scripts/production_date.py with no network: a fake
GitHub answers its `gh api` calls from the recorded fixtures in
scripts/fixtures/production-date/, paging and filtering the way GitHub does.

Run: python3 scripts/production-date.test.py
"""
import copy
import datetime
import json
import os
import subprocess
import sys
import unittest
from urllib.parse import parse_qs, urlsplit

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
        parts = url.path.split("/")
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
            return {"ref": "refs/tags/" + name}
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
        tags = {t: sha for t, sha in self.fx.get("tag_commits", {}).items()}
        base, head = tags.get(base, base), tags.get(head, head)
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
        self.assertIn("#46", result["reason"])

    def test_an_unmerged_pr_hasnt_landed(self):
        result, _ = find(load("stacked"), "merge", [43, 49])
        self.assertEqual(result["status"], "held")
        self.assertIn("isn't merged", [p for p in result["prs"] if p["pr"] == 49][0]["reason"])

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
