#!/usr/bin/env python3
"""Tests skills/release-notes/scripts/catch_up.py with no network: a fake Jira
answers the REST search from a recorded fixture, one page per nextPageToken,
and a fake `gh` answers the GitHub searches from another, returning at most
--limit results the way `gh issue list` does.

Run: python3 scripts/catch-up.test.py
"""
import contextlib
import copy
import io
import json
import os
import sys
import unittest
import urllib.error
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "skills", "release-notes", "scripts", "catch_up.py")
FIXTURES = os.path.join(ROOT, "scripts", "fixtures", "catch-up")
sys.path.insert(0, os.path.dirname(SCRIPT))

import base64  # noqa: E402

import catch_up  # noqa: E402


def load(name):
    with open(os.path.join(FIXTURES, name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def keys(items):
    return [i["key"] for i in items]


def reasons(result):
    return {d["key"]: d["reason"] for d in result["dropped"]}


class Jira(unittest.TestCase):
    def sort(self, pages, done="Done", ready="Ready for Release"):
        return catch_up.sort_jira(pages, done=done, ready=ready)

    def test_epics_candidates_and_dropped(self):
        r = self.sort(load("jira-two-pages")["pages"])
        self.assertEqual(keys(r["epics"]), ["PROJ-2470", "PROJ-2480"])
        self.assertEqual(keys(r["candidates"]), ["PROJ-2501", "PROJ-2510"])
        self.assertEqual(r["candidates"][0]["type"], "bug")
        why = reasons(r)
        self.assertEqual(set(why), {"PROJ-2472", "PROJ-2475", "PROJ-2520"})
        self.assertIn("sub-task of PROJ-2471", why["PROJ-2472"])
        self.assertIn("Test", why["PROJ-2475"])
        self.assertIn("moved back to To Do", why["PROJ-2520"])

    def test_a_slice_counts_toward_its_epic_even_when_the_epic_isnt_listed(self):
        r = self.sort(load("jira-two-pages")["pages"])
        self.assertIn({"key": "PROJ-2481", "epic": "PROJ-2480"}, r["children"])
        self.assertIn({"key": "PROJ-2471", "epic": "PROJ-2470"}, r["children"])
        self.assertEqual(r["epics"][1]["title"], "Download costs as a spreadsheet")

    def test_a_ticket_on_two_pages_counts_once(self):
        r = self.sort(load("jira-two-pages")["pages"])
        self.assertEqual(keys(r["epics"]).count("PROJ-2470"), 1)

    def test_every_page_read(self):
        r = self.sort(load("jira-two-pages")["pages"])
        self.assertTrue(r["complete"])
        self.assertIsNone(r["reason"])

    def test_a_missing_last_page_is_said(self):
        pages = load("jira-two-pages")["pages"][:1]
        r = self.sort(pages)
        self.assertFalse(r["complete"])
        self.assertIn("page 1", r["reason"])
        self.assertIn("nextPageToken", r["reason"])

    def test_status_names_match_whatever_their_case(self):
        r = self.sort(load("jira-two-pages")["pages"], done="done", ready="READY FOR RELEASE")
        self.assertNotIn("PROJ-2510", reasons(r))

    def page(self, *issues):
        return [{"issues": list(issues), "isLast": True}]

    def issue(self, key, kind="Story", status="Done", category="done", parent=None, level=0,
              subtask=False, resolution=None, parent_status=None):
        f = {"summary": key, "issuetype": {"name": kind, "subtask": subtask, "hierarchyLevel": level},
             "status": {"name": status, "statusCategory": {"key": category}}}
        if resolution:
            f["resolution"] = {"name": resolution}
        if parent:
            f["parent"] = {"key": parent[0], "fields": {"summary": parent[0],
                           "issuetype": {"name": parent[1], "hierarchyLevel": parent[2]}}}
            if parent_status:
                f["parent"]["fields"]["status"] = {"name": parent_status, "statusCategory": {"key": "done"}}
        return {"key": key, "fields": f}

    def test_a_ticket_closed_without_shipping_is_dropped(self):
        r = self.sort(self.page(self.issue("P-1", kind="Bug", status="Won't Do"),
                                self.issue("P-2", kind="Bug", status="Closed", resolution="Duplicate")))
        self.assertEqual(r["candidates"], [])
        self.assertIn("Won't Do", reasons(r)["P-1"])
        self.assertIn("Duplicate", reasons(r)["P-2"])

    def test_a_slice_of_a_cancelled_epic_is_dropped(self):
        r = self.sort(self.page(self.issue("P-2", parent=("P-1", "Epic", 1), parent_status="Cancelled")))
        self.assertEqual(r["epics"], [])
        self.assertIn("P-1", reasons(r)["P-2"])

    def test_an_xray_pre_condition_is_dropped(self):
        r = self.sort(self.page(self.issue("P-1", kind="Pre-Condition")))
        self.assertEqual(r["candidates"], [])

    def test_an_issue_without_fields_doesnt_crash(self):
        r = self.sort([{"issues": [{"key": "P-1"}], "isLast": True}])
        self.assertIn("P-1", reasons(r))

    def test_without_a_ready_status_a_done_category_status_still_counts(self):
        r = self.sort(self.page(self.issue("P-1", kind="Bug", status="Ready for Release")), ready=None)
        self.assertEqual(keys(r["candidates"]), ["P-1"])

    def test_a_ticket_moved_on_to_another_done_status_is_kept(self):
        r = self.sort(self.page(self.issue("P-1", kind="Bug", status="Released")))
        self.assertEqual(keys(r["candidates"]), ["P-1"])

    def test_a_parent_at_the_epic_level_counts_whatever_its_name(self):
        r = self.sort(self.page(self.issue("P-2", parent=("P-1", "Feature", 1))))
        self.assertEqual(keys(r["epics"]), ["P-1"])
        self.assertEqual(r["candidates"], [])

    def test_xray_test_types_are_dropped(self):
        r = self.sort(self.page(*[self.issue(f"P-{i}", kind=k) for i, k in
                                  enumerate(["Test Execution", "Test Plan", "Test Set", "Precondition"])]))
        self.assertEqual(r["candidates"], [])
        self.assertEqual(len(r["dropped"]), 4)

    def test_a_slice_of_an_epic_that_moved_back_doesnt_bring_it_back(self):
        r = self.sort(self.page(self.issue("P-2", parent=("P-1", "Epic", 1)),
                                self.issue("P-1", kind="Epic", level=1, status="To Do", category="new")))
        self.assertEqual(r["epics"], [])
        self.assertIn("P-1", reasons(r)["P-2"])

    def test_pages_short_of_their_total_are_incomplete(self):
        pages = [{"startAt": 0, "maxResults": 2, "total": 3,
                  "issues": [self.issue("P-1", kind="Bug"), self.issue("P-2", kind="Bug")]}]
        r = self.sort(pages)
        self.assertFalse(r["complete"])
        self.assertIn("2 of 3", r["reason"])

    def test_pages_that_reach_their_total_are_complete(self):
        pages = [{"startAt": 0, "maxResults": 1, "total": 2, "issues": [self.issue("P-1", kind="Bug")]},
                 {"startAt": 1, "maxResults": 1, "total": 2, "issues": [self.issue("P-2", kind="Bug")]}]
        self.assertTrue(self.sort(pages)["complete"])

    def test_a_status_outside_done_is_moved_back(self):
        r = self.sort(self.page(self.issue("P-1", kind="Bug", status="In Review", category="indeterminate")))
        self.assertIn("moved back to In Review", reasons(r)["P-1"])


class FakeJira:
    """Answers catch_up's post(url, body, headers) calls from the Jira pages
    fixture: the first page for a request with no nextPageToken, and the page
    after the one that handed out the token otherwise."""

    def __init__(self, pages, error=None):
        self.pages = pages
        self.error = error
        self.calls = []

    def __call__(self, url, body, headers):
        self.calls.append({"url": url, "body": body, "headers": headers})
        if self.error:
            raise catch_up.JiraError(self.error)
        token = body.get("nextPageToken")
        if not token:
            return copy.deepcopy(self.pages[0])
        for n, page in enumerate(self.pages):
            if page.get("nextPageToken") == token:
                return copy.deepcopy(self.pages[n + 1])
        raise AssertionError(f"unknown nextPageToken: {token}")


class JiraRest(unittest.TestCase):
    def search(self, fake, site="acme.atlassian.net"):
        return catch_up.search_jira(site, "PROJ", "2026-02-01", done="Done",
                                    ready="Ready for Release", email="dev@acme.example",
                                    token="t0ken", post=fake)

    def test_every_page_is_read(self):
        fake = FakeJira(load("jira-two-pages")["pages"])
        r = self.search(fake)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(fake.calls[1]["body"]["nextPageToken"], "page-2")
        self.assertEqual(keys(r["epics"]), ["PROJ-2470", "PROJ-2480"])
        self.assertEqual(keys(r["candidates"]), ["PROJ-2501", "PROJ-2510"])
        self.assertTrue(r["complete"])

    def test_the_search_asks_for_moves_since_the_date_and_only_the_fields_it_uses(self):
        fake = FakeJira(load("jira-two-pages")["pages"])
        self.search(fake, site="https://acme.atlassian.net/")
        call = fake.calls[0]
        self.assertEqual(call["url"], "https://acme.atlassian.net/rest/api/3/search/jql")
        self.assertEqual(call["body"]["jql"],
                         'project = "PROJ" AND status CHANGED TO ("Done", "Ready for Release") '
                         'AFTER "2026-02-01" ORDER BY updated ASC')
        self.assertEqual(sorted(call["body"]["fields"]),
                         ["issuetype", "parent", "resolution", "status", "summary"])
        self.assertEqual(call["body"]["maxResults"], 100)
        self.assertEqual(call["headers"]["Authorization"],
                         "Basic " + base64.b64encode(b"dev@acme.example:t0ken").decode())

    def test_a_repeated_page_token_stops_the_search_as_incomplete(self):
        pages = load("jira-two-pages")["pages"]
        pages[1]["nextPageToken"] = "page-2"
        pages[1].pop("isLast")
        fake = FakeJira(pages)
        r = self.search(fake)
        self.assertEqual(len(fake.calls), 2)
        self.assertFalse(r["complete"])
        self.assertIn("nextPageToken", r["reason"])

    def test_a_refused_search_says_so_without_the_token(self):
        with self.assertRaises(catch_up.JiraError) as e:
            self.search(FakeJira([], error="Jira said 401 Unauthorized"))
        self.assertIn("401", str(e.exception))
        self.assertNotIn("t0ken", str(e.exception))


    def test_a_401_from_jira_says_to_check_the_token(self):
        refused = urllib.error.HTTPError("https://acme.atlassian.net/rest/api/3/search/jql",
                                         401, "Unauthorized", {}, None)
        with mock.patch("urllib.request.urlopen", side_effect=refused), \
                self.assertRaises(catch_up.JiraError) as e:
            catch_up.post("https://acme.atlassian.net/rest/api/3/search/jql", {}, {})
        self.assertIn("401", str(e.exception))
        self.assertIn("JIRA_API_TOKEN", str(e.exception))

class FakeGh:
    """Answers catch_up's gh(args) calls from the github fixture. A search
    returns at most --limit results, as `gh issue list` does; `big` maps a
    search string to how many made-up issues it should return instead."""

    def __init__(self, fixture, big=None):
        self.fx = fixture
        self.big = big or {}
        self.calls = []

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ["issue", "list"]:
            search = args[args.index("--search") + 1]
            limit = int(args[args.index("--limit") + 1])
            if search in self.big:
                n = self.big[search]
                made = [{"number": 1000 + i, "title": f"Issue {i}", "state": "CLOSED",
                         "stateReason": "COMPLETED", "closedAt": "2026-02-02T00:00:00Z",
                         "issueType": None, "labels": [{"name": "bug"}], "parent": None}
                        for i in range(n)]
                return made[:limit]
            if "reason:completed" in search:
                return copy.deepcopy(self.fx["closed"])[:limit]
            return copy.deepcopy(self.fx["ready"])[:limit]
        if args[:2] == ["issue", "view"]:
            return copy.deepcopy(self.fx["issues"][args[2]])
        if args[0] == "api":
            n = args[-1].split("/")[-2]
            return copy.deepcopy(self.fx["timelines"].get(n, [[]]))
        raise AssertionError(f"unexpected gh call: {args}")


class GitHub(unittest.TestCase):
    def run_github(self, fake, since="2026-02-01", today="2026-03-01"):
        return catch_up.search_github("acme/acme-skills", since=since, today=today,
                                      ready_label="Ready for Release", gh=fake)

    def test_closed_and_ready_since_the_date(self):
        r = self.run_github(FakeGh(load("github")))
        self.assertEqual(keys(r["epics"]), ["#90", "#97"])
        self.assertEqual(keys(r["candidates"]), ["#95"])
        self.assertEqual(r["candidates"][0]["type"], "bug")
        self.assertIn({"key": "#91", "epic": "#90"}, r["children"])
        self.assertIn({"key": "#96", "epic": "#97"}, r["children"])
        self.assertTrue(r["complete"])

    def test_a_kind_label_wins_over_an_issue_type(self):
        fx = load("github")
        fx["issues"]["90"]["issueType"] = {"name": "Feature"}
        r = self.run_github(FakeGh(fx))
        self.assertIn({"key": "#91", "epic": "#90"}, r["children"])

    def test_a_sub_issue_of_a_story_is_dropped(self):
        r = self.run_github(FakeGh(load("github")))
        self.assertIn("sub-task of #91", reasons(r)["#93"])

    def test_labelled_ready_before_the_date_is_dropped(self):
        r = self.run_github(FakeGh(load("github")))
        self.assertIn("2026-01-20", reasons(r)["#98"])

    def test_the_closed_search_asks_for_completed_issues_since_the_date(self):
        fake = FakeGh(load("github"))
        self.run_github(fake)
        searches = [c[c.index("--search") + 1] for c in fake.calls if c[:2] == ["issue", "list"]]
        self.assertIn("closed:2026-02-01..2026-03-01 reason:completed", searches)
        limits = {c[c.index("--limit") + 1] for c in fake.calls if c[:2] == ["issue", "list"]}
        self.assertEqual(limits, {"1000"})

    def test_a_search_at_its_limit_is_split_by_date(self):
        big = {"closed:2026-02-01..2026-03-01 reason:completed": 1000,
               "closed:2026-02-01..2026-02-15 reason:completed": 400,
               "closed:2026-02-16..2026-03-01 reason:completed": 300}
        fake = FakeGh(load("github"), big=big)
        r = self.run_github(fake)
        self.assertTrue(r["complete"])
        searches = [c[c.index("--search") + 1] for c in fake.calls if c[:2] == ["issue", "list"]]
        self.assertIn("closed:2026-02-01..2026-02-15 reason:completed", searches)
        self.assertIn("closed:2026-02-16..2026-03-01 reason:completed", searches)

    def test_a_ready_search_at_its_limit_is_split_by_date(self):
        big = {'label:"Ready for Release" updated:2026-02-01..2026-03-01': 1000,
               'label:"Ready for Release" updated:2026-02-01..2026-02-15': 400,
               'label:"Ready for Release" updated:2026-02-16..2026-03-01': 300}
        fake = FakeGh(load("github"), big=big)
        r = self.run_github(fake)
        self.assertTrue(r["complete"], r["reason"])
        searches = [c[c.index("--search") + 1] for c in fake.calls if c[:2] == ["issue", "list"]]
        self.assertIn('label:"Ready for Release" updated:2026-02-16..2026-03-01', searches)

    def test_the_ready_search_is_bounded_by_the_date(self):
        fake = FakeGh(load("github"))
        self.run_github(fake)
        searches = [c[c.index("--search") + 1] for c in fake.calls if c[:2] == ["issue", "list"]]
        self.assertIn('label:"Ready for Release" updated:2026-02-01..2026-03-01', searches)

    def test_a_ready_issue_with_no_labelled_event_is_noted(self):
        fx = load("github")
        fx["timelines"]["96"] = [[]]
        r = self.run_github(FakeGh(fx))
        self.assertTrue(any("#96" in n for n in r["notes"]))

    def test_both_limit_reasons_are_kept(self):
        big = {"closed:2026-02-01..2026-02-01 reason:completed": 1000,
               'label:"Ready for Release" updated:2026-02-01..2026-02-01': 1000}
        r = self.run_github(FakeGh(load("github"), big=big), today="2026-02-01")
        self.assertIn("2026-02-01", r["reason"])
        self.assertIn("label", r["reason"])

    def test_a_ready_issue_closed_as_not_planned_is_dropped(self):
        fx = load("github")
        fx["ready"][0].update(state="CLOSED", stateReason="NOT_PLANNED")
        r = self.run_github(FakeGh(fx))
        self.assertIn("not planned", reasons(r)["#96"])

    def test_a_ready_issue_closed_as_a_duplicate_is_dropped(self):
        fx = load("github")
        fx["ready"][0].update(state="CLOSED", stateReason="DUPLICATE")
        r = self.run_github(FakeGh(fx))
        self.assertIn("duplicate", reasons(r)["#96"])
        self.assertNotIn({"key": "#96", "epic": "#97"}, r["children"])

    def test_a_story_of_an_epic_closed_as_not_planned_is_dropped(self):
        fx = load("github")
        fx["issues"]["97"].update(state="CLOSED", stateReason="NOT_PLANNED")
        fake = FakeGh(fx)
        r = self.run_github(fake)
        self.assertNotIn("#97", keys(r["epics"]))
        self.assertIn("#97", reasons(r)["#96"])
        views = [c for c in fake.calls if c[:2] == ["issue", "view"]]
        self.assertTrue(all("stateReason" in c[c.index("--json") + 1] for c in views))

    def test_a_story_under_a_parent_of_unknown_kind_is_a_candidate(self):
        fx = load("github")
        fx["issues"]["91"].update(labels=[], issueType=None)
        r = self.run_github(FakeGh(fx))
        self.assertIn("#93", keys(r["candidates"]))
        self.assertNotIn("#93", reasons(r))
        self.assertTrue(any("#93" in n and "#91" in n for n in r["notes"]))

    def test_both_halves_limit_reasons_are_kept(self):
        big = {"closed:2026-02-01..2026-02-02 reason:completed": 1000,
               "closed:2026-02-01..2026-02-01 reason:completed": 1000,
               "closed:2026-02-02..2026-02-02 reason:completed": 1000}
        r = self.run_github(FakeGh(load("github"), big=big), today="2026-02-02")
        self.assertIn("2026-02-01", r["reason"])
        self.assertIn("2026-02-02", r["reason"])

    def test_a_test_type_reason_names_the_type(self):
        fx = load("github")
        fx["closed"][3]["issueType"] = {"name": "Test Plan"}
        r = self.run_github(FakeGh(fx))
        self.assertIn("Test Plan", reasons(r)["#95"])

    def test_output_that_isnt_json_is_a_gh_error(self):
        with self.assertRaises(catch_up.GhError):
            catch_up.parse("gh issue list", "a new version of gh is available")

    def test_one_day_at_the_limit_is_said(self):
        big = {f"closed:{d}..{d} reason:completed": 1000 for d in ["2026-02-01"]}
        big["closed:2026-02-01..2026-02-01 reason:completed"] = 1000
        fake = FakeGh(load("github"), big=big)
        r = self.run_github(fake, since="2026-02-01", today="2026-02-01")
        self.assertFalse(r["complete"])
        self.assertIn("2026-02-01", r["reason"])


class Cutoff(unittest.TestCase):
    def test_live_before_the_date_is_dropped_and_the_rest_sorted_oldest_first(self):
        features = [
            {"key": "PROJ-2400", "status": "dated", "date": "2026-03-03"},
            {"key": "PROJ-2450", "status": "dated", "date": "2026-01-28"},
            {"key": "PROJ-2470", "status": "dated", "date": "2026-02-20"},
            {"key": "PROJ-2490", "status": "held"},
            {"key": "PROJ-2495", "status": "not_found"},
        ]
        r = catch_up.cut_off(features, since="2026-02-01")
        self.assertEqual(keys(r["notes"]), ["PROJ-2470", "PROJ-2400", "PROJ-2490", "PROJ-2495"])
        self.assertEqual(r["dropped"], [{"key": "PROJ-2450",
                                         "reason": "live 2026-01-28, before 2026-02-01"}])

    def test_live_on_the_date_is_kept(self):
        r = catch_up.cut_off([{"key": "A", "status": "dated", "date": "2026-02-01"}], since="2026-02-01")
        self.assertEqual(keys(r["notes"]), ["A"])


class Cli(unittest.TestCase):
    def main(self, argv, stdin=""):
        out = io.StringIO()
        old = sys.stdin
        sys.stdin = io.StringIO(stdin)
        try:
            with contextlib.redirect_stdout(out):
                code = catch_up.main(argv)
        finally:
            sys.stdin = old
        return code, json.loads(out.getvalue())

    JIRA = ["jira", "--site", "acme.atlassian.net", "--project", "PROJ", "--since", "2026-02-01",
            "--done", "Done", "--ready", "Ready for Release"]

    def test_jira_searches_with_the_token_from_the_environment(self):
        fake = FakeJira(load("jira-two-pages")["pages"])
        env = {"JIRA_EMAIL": "dev@acme.example", "JIRA_API_TOKEN": "t0ken"}
        with mock.patch.dict(os.environ, env), mock.patch.object(catch_up, "post", fake):
            code, r = self.main(self.JIRA)
        self.assertEqual(code, 0)
        self.assertEqual(keys(r["epics"]), ["PROJ-2470", "PROJ-2480"])

    def test_jira_without_a_token_stops_and_says_what_to_set(self):
        fake = FakeJira(load("jira-two-pages")["pages"])
        err = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(catch_up, "post", fake), \
                contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            code = catch_up.main(self.JIRA)
        self.assertEqual(code, 2)
        self.assertEqual(fake.calls, [])
        self.assertIn("JIRA_EMAIL", err.getvalue())
        self.assertIn("JIRA_API_TOKEN", err.getvalue())

    def test_jira_no_longer_takes_page_files(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            catch_up.main(["jira", "--done", "Done", "p1.json"])

    def test_a_failed_jira_search_exits_1(self):
        env = {"JIRA_EMAIL": "dev@acme.example", "JIRA_API_TOKEN": "t0ken"}
        with mock.patch.dict(os.environ, env), \
                mock.patch.object(catch_up, "post", FakeJira([], error="Jira said 403 Forbidden")):
            code, r = self.main(self.JIRA)
        self.assertEqual(code, 1)
        self.assertFalse(r["complete"])
        self.assertIn("403", r["reason"])

    def test_cutoff_reads_stdin(self):
        code, r = self.main(["cutoff", "--since", "2026-02-01"],
                            json.dumps([{"key": "A", "status": "dated", "date": "2026-01-02"}]))
        self.assertEqual(code, 0)
        self.assertEqual(keys(r["dropped"]), ["A"])


if __name__ == "__main__":
    unittest.main()
