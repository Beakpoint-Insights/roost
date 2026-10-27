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
from urllib.parse import quote

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

def landing(repo, owner, default, number, gh, branches):
    """The PR that brought PR `number`'s change onto the default branch."""
    pr = read(gh, f"repos/{repo}/pulls/{number}", f"#{number}")
    entry = {"pr": number, "base": pr["base"]["ref"]}
    if not pr.get("merged_at"):
        return dict(entry, landed=False, reason=f"#{number} isn't merged")
    sha = pr["merge_commit_sha"]
    current = pr
    for _ in range(MAX_STACK):
        base = current["base"]["ref"]
        if base == default:
            return dict(entry, landing_pr=current["number"], landing_sha=current["merge_commit_sha"],
                        landed_at=current["merged_at"])
        # On a stack: it lands with the first PR from its base branch that merged after it and
        # whose head holds it (a branch name can be reused). Not by its merge commit, which a
        # squash merge leaves out of the default branch's history.
        if base not in branches:
            branches[base] = pulls_from(repo, owner, base, gh)
        later = sorted((p for p in branches[base] if p.get("merged_at") and p["merged_at"] >= current["merged_at"]),
                       key=lambda p: p["merged_at"])
        current = next((p for p in later if contains(repo, sha, p["head"]["sha"], gh)), None)
        if current is None:
            if contains(repo, sha, default, gh):
                raise NotFound(f"#{number} reached `{default}` from `{base}` without a PR, "
                               f"so when it landed isn't known")
            return dict(entry, landed=False,
                        reason=f"#{number} merged into `{base}`, and no PR has brought it onto `{default}`")
    raise NotFound(f"#{number}'s stack is deeper than {MAX_STACK} branches")


def pulls_from(repo, owner, branch, gh):
    head = quote(f"{owner}:{branch}", safe=":")
    found, page = [], 1
    while True:
        batch = read(gh, f"repos/{repo}/pulls?state=closed&head={head}&per_page={PER_PAGE}&page={page}",
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
        branches = {}
        result["prs"] = [landing(repo, owner, default, n, gh, branches) for n in prs]
        landed = [p for p in result["prs"] if p.get("landed") is not False]
        waiting = [p for p in result["prs"] if p.get("landed") is False]
        if landed:
            last = max(landed, key=lambda p: p["landed_at"])
            result["last_change"] = {k: last[k] for k in ("pr", "landing_pr", "landing_sha", "landed_at")}
        if production is None:
            raise NotFound("; ".join([f"{repo} has no `production` in the config"]
                                     + [p["reason"] + ": not on the default branch yet" for p in waiting]))
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
    except (KeyError, TypeError, ValueError, AttributeError) as e:
        result.update(status="not_found", date=None, time=None,
                      reason=f"unexpected answer from gh ({type(e).__name__}: {e}); run it again, or check by hand")
    return result


def contains(repo, sha, head, gh):
    """`compare`'s status if `head` contains `sha` (ahead or identical), else None."""
    status = read(gh, f"repos/{repo}/compare/{sha}...{head}", f"whether {head} contains {sha}")["status"]
    return status if status in ("ahead", "identical") else None


def by_workflow(repo, default, workflow, last, today, gh):
    """The first successful run on the default branch or a tag whose commit contains the
    landing commit, searched in day windows from the day before it landed to `today`."""
    try:
        gh(f"repos/{repo}/actions/workflows/{workflow}")
    except GhError as e:
        raise NotFound(f"gh couldn't read the workflow `{workflow}` ({e}); check `production`'s workflow")
    tags = {}

    def deploys(run):
        if run["conclusion"] != "success" or run["event"] in ("pull_request", "pull_request_target"):
            return False
        branch = run["head_branch"]
        if branch == default:
            return True
        if branch not in tags:
            try:
                gh(f"repos/{repo}/git/ref/tags/{branch}")
                tags[branch] = True
            except GhError as e:
                if "404" not in str(e):
                    raise NotFound(f"gh couldn't read whether `{branch}` is a tag: {e}")
                tags[branch] = False
        return tags[branch]

    one_day = datetime.timedelta(days=1)
    start = utc_day(last["landed_at"]) - one_day
    deployed_before = False
    while start <= today:
        end = today
        while True:
            runs, capped = list_runs(repo, workflow, f"&created={start}..{end}", gh)
            if not capped:
                break
            if start == end:
                raise NotFound(f"page limit: GitHub lists at most {SEARCH_LIMIT} `{workflow}` runs for one search, "
                               f"and {start} has more")
            end = start + (end - start) // 2
        for run in sorted(filter(deploys, runs), key=lambda r: r["created_at"]):
            deployed_before = True
            status = contains(repo, last["landing_sha"], run["head_sha"], gh)
            if status:
                attempt, finished = first_success(repo, run, gh)
                return ({"kind": "workflow", "workflow": workflow, "run_id": run["id"], "url": run["html_url"],
                         "head_sha": run["head_sha"], "head_branch": run["head_branch"], "event": run["event"],
                         "attempt": attempt,
                         "matched": f"compare {last['landing_sha']}...{run['head_sha']}: {status}"},
                        finished)
        start = end + one_day
    if deployed_before or ever_deployed(repo, workflow, deploys, gh):
        return None, None
    raise NotFound(f"no successful `{workflow}` runs on the default branch or a tag; check `production`'s workflow")


def list_runs(repo, workflow, created, gh):
    """(runs, capped): a workflow's successful runs, every page; capped when GitHub
    has more than one search returns."""
    runs, page = [], 1
    while True:
        body = read(gh, f"repos/{repo}/actions/workflows/{workflow}/runs?status=success{created}"
                        f"&per_page={PER_PAGE}&page={page}", f"`{workflow}`'s runs")
        if body["total_count"] >= SEARCH_LIMIT:
            return runs, True
        runs += body["workflow_runs"]
        if len(body["workflow_runs"]) < PER_PAGE:
            return runs, False
        page += 1


def ever_deployed(repo, workflow, deploys, gh):
    """Whether any successful run, ever, ran on the default branch or a tag."""
    for page in range(1, SEARCH_LIMIT // PER_PAGE + 1):
        body = read(gh, f"repos/{repo}/actions/workflows/{workflow}/runs?status=success"
                        f"&per_page={PER_PAGE}&page={page}", f"`{workflow}`'s runs")
        if any(map(deploys, body["workflow_runs"])):
            return True
        if len(body["workflow_runs"]) < PER_PAGE:
            return False
    raise NotFound(f"page limit: none of `{workflow}`'s newest {SEARCH_LIMIT} successful runs ran on the "
                   f"default branch or a tag, and GitHub lists no more")


def first_success(repo, run, gh):
    """(attempt, finished at) of the run's first successful attempt: a run can succeed
    only on a re-run, or finish the day after it started."""
    for n in range(1, run["run_attempt"] + 1):
        attempt = read(gh, f"repos/{repo}/actions/runs/{run['id']}/attempts/{n}", f"run {run['id']}'s attempts")
        if attempt["conclusion"] == "success":
            return n, attempt["updated_at"]
    raise NotFound(f"run {run['id']} is listed as successful, but none of its attempts succeeded")


def by_release(repo, last, today, gh):
    """The first published release, by publish date, whose tag contains the landing commit.
    The API lists releases by when each was created, so every page is read and sorted here."""
    since = (utc_day(last["landed_at"]) - datetime.timedelta(days=1)).isoformat()
    releases, page = [], 1
    while True:
        batch = read(gh, f"repos/{repo}/releases?per_page={PER_PAGE}&page={page}", "the releases")
        releases += batch
        if len(batch) < PER_PAGE:
            break
        page += 1
    published = [r for r in releases if not r["draft"] and not r["prerelease"] and r["published_at"]
                 and since <= r["published_at"][:10] <= today.isoformat()]
    for r in sorted(published, key=lambda r: r["published_at"]):
        status = contains(repo, last["landing_sha"], r["tag_name"], gh)
        if status:
            return ({"kind": "release", "tag": r["tag_name"], "url": r["html_url"], "published_at": r["published_at"],
                     "matched": f"compare {last['landing_sha']}...{r['tag_name']}: {status}"},
                    r["published_at"])
    return None, None


def deploy_for(repo, default, production, last, today, gh):
    """(deploy, time) for the first production deploy carrying `last`, or (None, None)."""
    if production == "merge":
        return by_merge(last)
    if isinstance(production, dict) and "workflow" in production:
        return by_workflow(repo, default, production["workflow"], last, today, gh)
    if production == "release":
        return by_release(repo, last, today, gh)
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
                   help="the last day to look for a deploy or release, YYYY-MM-DD (default: today, UTC)")
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
