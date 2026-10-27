#!/usr/bin/env python3
"""Sorts the tickets a release-notes catch-up starts from, and drops what was
live before the date.

Usage:
  catch_up.py jira --done NAME [--ready NAME] PAGE.json [PAGE.json ...]
  catch_up.py github --repo OWNER/NAME --since YYYY-MM-DD [--ready-label NAME]
                     [--today YYYY-MM-DD]
  catch_up.py cutoff --since YYYY-MM-DD < features.json

jira:    give it every page the Jira search for tickets moved to done or ready
         for release since the date returned, in order, each as saved from
         the search (its `issues`, and `nextPageToken` or `isLast`).
github:  it runs the searches itself with `gh`: issues closed as completed
         since the date, and issues labelled ready for release since then.

Both print one JSON object:
  complete    false when the search wasn't read in full, with the reason
  reason      why it isn't complete, as a line for the checks, or null
  epics       [{key, title}] each epic with work moved since the date, in the
              order the search returned them
  candidates  [{key, type, title}] standalone stories, tasks and bugs
  children    [{key, epic}] slices whose work counts toward their epic
  dropped     [{key, reason}] Tests, sub-tasks, and tickets moved back out
              of done, with the reason, for the checks

cutoff:  give it each feature's production_date.py result with its key,
         [{key, status, date, ...}], on stdin. It prints {notes, dropped}:
         notes oldest first (held and not-found ones after the dated ones),
         and dropped, the features live before the date, with the reason.

Exit 0 whatever it finds; 2 for bad arguments, and 1 when `gh` fails (still
with the JSON, complete false, naming the error).
"""
import argparse
import datetime
import json
import subprocess
import sys

LIMIT = 1000  # GitHub's search returns at most this many results
KINDS = ("epic", "story", "task", "bug", "test")


class GhError(Exception):
    """`gh` couldn't read something; the message says what and why."""


def gh(args):
    """Runs `gh` with args and returns its parsed JSON output."""
    try:
        out = subprocess.run(["gh"] + args, capture_output=True, text=True)
    except OSError as e:
        raise GhError(f"can't run gh: {e}")
    if out.returncode != 0:
        raise GhError(f"gh {' '.join(args[:2])}: {(out.stderr or out.stdout).strip()}")
    return json.loads(out.stdout)


def result():
    return {"complete": True, "reason": None, "epics": [], "candidates": [],
            "children": [], "dropped": []}


def add_epic(r, key, title):
    if key not in [e["key"] for e in r["epics"]]:
        r["epics"].append({"key": key, "title": title})


# ---------- Jira ----------

def sort_jira(pages, done, ready=None):
    """Sorts a Jira search's pages into epics, candidates, children and dropped."""
    r = result()
    for n, page in enumerate(pages, 1):
        if n == len(pages) and page.get("nextPageToken") and not page.get("isLast"):
            r["complete"] = False
            r["reason"] = (f"page {n} has a nextPageToken: the search wasn't read "
                           "to its last page")
    kept = {s.lower() for s in (done, ready) if s}
    seen = set()
    for page in pages:
        for issue in page.get("issues", []):
            key = issue["key"]
            if key in seen:
                continue
            seen.add(key)
            f = issue.get("fields", {})
            kind = f.get("issuetype", {})
            status = f.get("status", {}).get("name", "")
            parent = f.get("parent")
            if kind.get("name", "").lower() == "test":
                r["dropped"].append({"key": key, "reason": "a Test, not customer work"})
            elif kind.get("subtask"):
                p = parent["key"] if parent else "its parent"
                r["dropped"].append({"key": key, "reason": f"sub-task of {p}: its work is part of {p}"})
            elif status.lower() not in kept:
                r["dropped"].append({"key": key, "reason": f"moved back to {status}"})
            elif kind.get("name", "").lower() == "epic" or kind.get("hierarchyLevel") == 1:
                add_epic(r, key, f.get("summary", ""))
            elif parent and parent.get("fields", {}).get("issuetype", {}).get("name", "").lower() == "epic":
                add_epic(r, parent["key"], parent["fields"].get("summary", ""))
                r["children"].append({"key": key, "epic": parent["key"]})
            else:
                r["candidates"].append({"key": key, "type": kind.get("name", "").lower(),
                                        "title": f.get("summary", "")})
    return r


# ---------- GitHub ----------

FIELDS = "number,title,state,stateReason,closedAt,issueType,labels,parent"


def kind_of(issue):
    """The issue's kind: its kind label (epic, story, task, bug, test) if it has
    one, else its issue type, as tracker-github.md writes kinds."""
    for label in issue.get("labels", []):
        if label["name"].lower() in KINDS:
            return label["name"].lower()
    if issue.get("issueType"):
        return issue["issueType"]["name"].lower()
    return ""


def closed_since(repo, start, end, gh):
    """Issues closed as completed from start to end, split by date at the limit.
    Returns (issues, reason), reason set when a single day is still at the limit."""
    search = f"closed:{start}..{end} reason:completed"
    found = gh(["issue", "list", "-R", repo, "--state", "closed", "--limit", str(LIMIT),
                "--search", search, "--json", FIELDS])
    if len(found) < LIMIT:
        return found, None
    a, b = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    if a == b:
        return found, (f"the search for issues closed on {start} returned its limit "
                       f"of {LIMIT}, and a day can't be split further")
    mid = a + (b - a) // 2
    left, why_l = closed_since(repo, start, mid.isoformat(), gh)
    right, why_r = closed_since(repo, (mid + datetime.timedelta(days=1)).isoformat(), end, gh)
    return left + right, why_l or why_r


def labelled_at(repo, number, label, gh):
    """When the label was last added to the issue, from its timeline, or None."""
    pages = gh(["api", "--paginate", "--slurp", f"repos/{repo}/issues/{number}/timeline"])
    times = [e["created_at"] for page in pages for e in page
             if e.get("event") == "labeled" and e.get("label", {}).get("name") == label]
    return max(times) if times else None


def search_github(repo, since, today, ready_label=None, gh=gh):
    """Sorts issues closed as completed, or labelled ready for release, since the date."""
    r = result()
    issues, why = closed_since(repo, since, today, gh)
    if why:
        r["complete"], r["reason"] = False, why
    if ready_label:
        ready = gh(["issue", "list", "-R", repo, "--state", "all", "--limit", str(LIMIT),
                    "--search", f'label:"{ready_label}"', "--json", FIELDS])
        if len(ready) >= LIMIT:
            r["complete"] = False
            r["reason"] = f'the search for label:"{ready_label}" returned its limit of {LIMIT}'
        numbers = {i["number"] for i in issues}
        for issue in ready:
            if issue["number"] in numbers:
                continue
            at = labelled_at(repo, issue["number"], ready_label, gh)
            if at and at[:10] < since:
                r["dropped"].append({"key": f"#{issue['number']}",
                                     "reason": f"labelled {ready_label} on {at[:10]}, before {since}"})
                continue
            issues.append(issue)
    parents = {}

    def parent_kind(number):
        if number not in parents:
            parents[number] = gh(["issue", "view", str(number), "-R", repo,
                                  "--json", "number,title,issueType,labels"])
        return kind_of(parents[number])

    for issue in issues:
        key, kind, parent = f"#{issue['number']}", kind_of(issue), issue.get("parent")
        if kind == "test":
            r["dropped"].append({"key": key, "reason": "a Test, not customer work"})
        elif kind == "epic":
            add_epic(r, key, issue["title"])
        elif parent and parent_kind(parent["number"]) == "epic":
            add_epic(r, f"#{parent['number']}", parents[parent["number"]]["title"])
            r["children"].append({"key": key, "epic": f"#{parent['number']}"})
        elif parent:
            p = f"#{parent['number']}"
            r["dropped"].append({"key": key, "reason": f"sub-task of {p}: its work is part of {p}"})
        else:
            r["candidates"].append({"key": key, "type": kind, "title": issue["title"]})
    r["epics"].sort(key=lambda e: int(e["key"][1:]))
    return r


# ---------- Cut-off ----------

def cut_off(features, since):
    """Drops features live before the date; the rest oldest first, undated last."""
    dated = [f for f in features if f.get("status") == "dated"]
    rest = [f for f in features if f.get("status") != "dated"]
    notes, dropped = [], []
    for f in sorted(dated, key=lambda f: f["date"]):
        if f["date"] < since:
            dropped.append({"key": f["key"], "reason": f"live {f['date']}, before {since}"})
        else:
            notes.append(f)
    return {"notes": notes + rest, "dropped": dropped}


def main(argv=None):
    p = argparse.ArgumentParser(description="Sort a release-notes catch-up's tickets.")
    sub = p.add_subparsers(dest="command", required=True)
    j = sub.add_parser("jira")
    j.add_argument("--done", required=True)
    j.add_argument("--ready")
    j.add_argument("pages", nargs="+")
    g = sub.add_parser("github")
    g.add_argument("--repo", required=True)
    g.add_argument("--since", required=True)
    g.add_argument("--ready-label")
    g.add_argument("--today", default=datetime.date.today().isoformat())
    c = sub.add_parser("cutoff")
    c.add_argument("--since", required=True)
    args = p.parse_args(argv)
    code = 0
    if args.command == "jira":
        pages = []
        for path in args.pages:
            with open(path, encoding="utf-8") as f:
                pages.append(json.load(f))
        out = sort_jira(pages, done=args.done, ready=args.ready)
    elif args.command == "github":
        try:
            out = search_github(args.repo, since=args.since, today=args.today,
                                ready_label=args.ready_label)
        except GhError as e:
            out, code = result(), 1
            out["complete"], out["reason"] = False, str(e)
    else:
        out = cut_off(json.load(sys.stdin), since=args.since)
    print(json.dumps(out, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
