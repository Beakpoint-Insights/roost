#!/usr/bin/env python3
"""Finds when production first carried a repo's last change for a feature, for
release-notes step 3 and close-out-epic.

Usage:
  production_date.py --repo OWNER/NAME (--workflow FILE | --release | --merge)
                     [--today YYYY-MM-DD] PR [PR ...]

Give it the feature's merged PRs in one repo and the repo's `production` (none
of the three options when the config has none). It finds where each PR landed
on the default branch, takes the last to land, and finds the first deploy,
release or merge that carried it, matching by commit, never by date.

It prints one JSON object and exits 0 whatever it finds (2 for bad arguments):
  status       "dated", "held" (production hasn't carried it yet) or
               "not_found" (the date can't be known)
  date, time   the UTC day and time customers could first use it, when dated
  reason       why it's held or not found, as a line for the checks
  last_change  {pr, landing_pr, landing_sha, landed_at}
  deploy       what carried it: {kind: "workflow", workflow, run_id, url,
               head_sha, head_branch, event, attempt, matched},
               {kind: "release", tag, url, published_at, matched} or
               {kind: "merge", pr, merged_at}
  prs          each PR: {pr, base, landing_pr, landing_sha, landed_at}, or
               {pr, base, landed: false, reason}
"""
import argparse
import datetime
import json
import re
import subprocess
import sys

PER_PAGE = 100
# GitHub returns at most this many workflow runs for a search filtered by
# `created` or `status` ("List workflow runs for a workflow").
SEARCH_LIMIT = 1000
# How far down a stack to follow base branches before giving up.
MAX_STACK = 20


class GhError(Exception):
    """`gh` couldn't read something; the message says what and why."""


class NotFound(Exception):
    """The date can't be known; the message is the reason."""


def gh_api(path):
    """GETs a GitHub API path with `gh api` and returns the parsed JSON."""
    try:
        out = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    except OSError as e:
        raise GhError(f"can't run gh: {e}")
    if out.returncode != 0:
        message = (out.stderr or out.stdout).strip()
        raise GhError(message.splitlines()[-1] if message else f"gh api {path} exited {out.returncode}")
    try:
        return json.loads(out.stdout)
    except ValueError as e:
        raise GhError(f"gh api {path} didn't return JSON: {e}")


def read(gh, path, what):
    try:
        return gh(path)
    except GhError as e:
        raise NotFound(f"gh couldn't read {what}: {e}")


def utc_day(timestamp):
    return datetime.date.fromisoformat(timestamp[:10])


# Landing: where each PR's change reached the default branch.

def landing(repo, owner, default, number, gh):
    """The PR that brought PR `number`'s change onto the default branch."""
    pr = read(gh, f"repos/{repo}/pulls/{number}", f"#{number}")
    entry = {"pr": number, "base": pr["base"]["ref"]}
    if not pr.get("merged_at"):
        return dict(entry, landed=False, reason=f"#{number} isn't merged")
    current = pr
    for _ in range(MAX_STACK):
        base = current["base"]["ref"]
        if base == default:
            return dict(entry, landing_pr=current["number"], landing_sha=current["merge_commit_sha"],
                        landed_at=current["merged_at"])
        # On a stack: it lands when the first PR from its base branch merged after it does.
        later = [p for p in pulls_from(repo, owner, base, gh)
                 if p.get("merged_at") and p["merged_at"] >= current["merged_at"]]
        if not later:
            return dict(entry, landed=False,
                        reason=f"#{number} merged into `{base}`, and no PR from `{base}` merged after it")
        current = min(later, key=lambda p: p["merged_at"])
    raise NotFound(f"#{number}'s stack is deeper than {MAX_STACK} branches")


def pulls_from(repo, owner, branch, gh):
    found, page = [], 1
    while True:
        batch = read(gh, f"repos/{repo}/pulls?state=closed&head={owner}:{branch}&per_page={PER_PAGE}&page={page}",
                     f"the PRs from `{branch}`")
        found += batch
        if len(batch) < PER_PAGE:
            return found
        page += 1


# The three ways to production.

def by_merge(last):
    return {"kind": "merge", "pr": last["landing_pr"], "merged_at": last["landed_at"]}, last["landed_at"]


def find(repo, production, prs, today, gh=gh_api):
    """The result described in the module docstring, as a dict."""
    result = {"repo": repo, "production": production, "status": None, "date": None, "time": None,
              "reason": None, "last_change": None, "deploy": None, "prs": []}
    try:
        default = read(gh, f"repos/{repo}", repo)["default_branch"]
        owner = repo.split("/")[0]
        result["prs"] = [landing(repo, owner, default, n, gh) for n in prs]
        landed = [p for p in result["prs"] if p.get("landed") is not False]
        waiting = [p for p in result["prs"] if p.get("landed") is False]
        if landed:
            last = max(landed, key=lambda p: p["landed_at"])
            result["last_change"] = {k: last[k] for k in ("pr", "landing_pr", "landing_sha", "landed_at")}
        if production is None:
            raise NotFound(f"{repo} has no `production` in the config")
        if landed:
            deploy, time = deploy_for(repo, default, production, result["last_change"], today, gh)
            result["deploy"] = deploy
        else:
            time = None
        if waiting:
            result["status"] = "held"
            result["reason"] = "; ".join(p["reason"] for p in waiting) + ": not on the default branch yet"
        elif time is None:
            result["status"] = "held"
            result["reason"] = held_reason(production, result["last_change"], today)
        else:
            result.update(status="dated", date=time[:10], time=time)
    except NotFound as e:
        result.update(status="not_found", date=None, time=None, reason=str(e))
    return result


def deploy_for(repo, default, production, last, today, gh):
    """(deploy, time) for the first production deploy carrying `last`, or (None, None)."""
    if production == "merge":
        return by_merge(last)
    raise NotFound(f"unknown production: {production!r}")


def held_reason(production, last, today):
    return f"no production deploy up to {today} contains #{last['landing_pr']} ({last['landing_sha']})"


# Command line.

def parse(argv):
    p = argparse.ArgumentParser(description="When production first carried a repo's last change for a feature.")
    p.add_argument("--repo", required=True, help="OWNER/NAME")
    way = p.add_mutually_exclusive_group()
    way.add_argument("--workflow", metavar="FILE", help="production is this workflow's successful runs")
    way.add_argument("--release", action="store_true", help="production is the published release")
    way.add_argument("--merge", action="store_true", help="merging to the default branch deploys")
    p.add_argument("--today", type=datetime.date.fromisoformat, default=None,
                   help="the search's last day, YYYY-MM-DD (default: today, UTC)")
    p.add_argument("prs", nargs="+", type=int, metavar="PR")
    args = p.parse_args(argv)
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", args.repo):
        p.error("--repo must be OWNER/NAME")
    return args


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)
    production = ({"workflow": args.workflow} if args.workflow else
                  "release" if args.release else "merge" if args.merge else None)
    today = args.today or datetime.datetime.now(datetime.timezone.utc).date()
    print(json.dumps(find(args.repo, production, args.prs, today), indent=2))


if __name__ == "__main__":
    main()
