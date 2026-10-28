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

It prints one JSON object and exits 0 whatever it finds; 2 is for bad arguments, and 1
for a failure of its own (still with the JSON, status not_found, naming the error):
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
DEEP = "deeper than"


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


def pages(gh, path, what):
    """Each page of a paged list, from the first until a short one. A page is a list,
    or for workflow runs an object with `workflow_runs` and `total_count`."""
    sep = "&" if "?" in path else "?"
    page = 1
    while True:
        body = read(gh, f"{path}{sep}per_page={PER_PAGE}&page={page}", what)
        yield body
        if len(body["workflow_runs"] if isinstance(body, dict) else body) < PER_PAGE:
            return
        page += 1


def failure_kind(error):
    """What kind of gh failure `error` is, in words, or None when its message doesn't say."""
    text = str(error).lower()
    if "rate limit" in text or "http 429" in text:
        return "GitHub's rate limit, so try again later"
    if "http 401" in text or "authentication" in text or "gh auth login" in text:
        return "a sign-in problem (check `gh auth status`)"
    if "http 404" in text or "not found" in text:
        return "not found"
    return None


def utc_day(timestamp):
    return datetime.date.fromisoformat(timestamp[:10])


# Landing: where each PR's change reached the default branch.

def landing(repo, owner, default, number, gh, branches, carried):
    """The PR that brought PR `number`'s change onto the default branch."""
    pr = read(gh, f"repos/{repo}/pulls/{number}", f"#{number}")
    entry = {"pr": number, "base": pr["base"]["ref"]}
    if not pr.get("merged_at"):
        return dict(entry, landed=False, reason=f"#{number} isn't merged")
    landed, trouble = carriers(repo, owner, default, pr, gh, branches, carried, 0)
    if landed:
        # More than one path can reach it (a branch merged into staging and into main): the first counts.
        first = min(landed, key=lambda p: p["merged_at"])
        return dict(entry, landing_pr=first["number"], landing_sha=first["merge_commit_sha"],
                    landed_at=first["merged_at"])
    if trouble:
        raise NotFound(f"#{number}: " + "; ".join(sorted(set(trouble))) + ", so when it landed isn't known")
    return dict(entry, landed=False,
                reason=f"#{number} merged into `{pr['base']['ref']}`, and no PR has brought it onto `{default}`")


def carriers(repo, owner, default, pr, gh, branches, carried, depth):
    """(landed, trouble): every PR, `pr` or one below it on the stack, that merged into the
    default branch with `pr`'s change, and why a path couldn't be followed."""
    if pr["number"] in carried:
        return carried[pr["number"]]
    base = pr["base"]["ref"]
    landed, trouble = [], []
    if base == default:
        landed = [pr]
    elif depth >= MAX_STACK:
        trouble = [f"its stack is {DEEP} {MAX_STACK} branches"]
    else:
        # On a stack: it lands with a PR from its base branch that merged after it and either
        # was open when it merged into that branch (a rebase rewrites the branch's commits) or
        # has a head that holds it, where its own base didn't already (the branch was kept and a
        # PR opened from it later). A PR from a reused branch name passes neither. Every such PR is followed: one may have
        # gone to another branch (staging) instead.
        if base not in branches:
            branches[base] = pulls_from(repo, owner, base, gh)
        merged = pr["merged_at"]
        for p in branches[base]:
            if not p.get("merged_at") or p["merged_at"] < merged:
                continue
            if p["created_at"] <= merged or head_carries(repo, pr["merge_commit_sha"], p, gh):
                more, why = carriers(repo, owner, default, p, gh, branches, carried, depth + 1)
                landed += more
                trouble += why
        if not landed and contains(repo, pr["merge_commit_sha"], default, gh):
            trouble.append(f"`{base}` reached `{default}`, but not through a PR that carried "
                           f"#{pr['number']} there")
    # A result the depth limit cut short depends on how deep it was reached: don't reuse it.
    if not any(DEEP in t for t in trouble):
        carried[pr["number"]] = (landed, trouble)
    return landed, trouble


def head_carries(repo, sha, p, gh):
    """Whether PR `p` brought commit `sha` with it: its head holds it, and the branch it merged
    into didn't already (`base.sha` is that branch as it was when `p` merged). A branch cut from
    main after the change got there holds it without carrying it."""
    if not contains(repo, sha, p["head"]["sha"], gh):
        return False
    return not (p["base"].get("sha") and contains(repo, sha, p["base"]["sha"], gh))


def pulls_from(repo, owner, branch, gh):
    head = quote(f"{owner}:{branch}", safe=":")
    return [p for body in pages(gh, f"repos/{repo}/pulls?state=closed&head={head}", f"the PRs from `{branch}`")
            for p in body]


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
        branches, carried = {}, {}
        for n in prs:
            result["prs"].append(landing(repo, owner, default, n, gh, branches, carried))
        landed = [p for p in result["prs"] if p.get("landed") is not False]
        waiting = [p for p in result["prs"] if p.get("landed") is False]
        if landed:
            last = max(landed, key=lambda p: p["landed_at"])
            result["last_change"] = {k: last[k] for k in ("pr", "landing_pr", "landing_sha", "landed_at")}
        if production is None:
            raise NotFound("; ".join([f"{repo} has no `production` in the config"]
                                     + [p["reason"] for p in waiting]))
        if landed:
            deploy, time = deploy_for(repo, default, production, result["last_change"], today, gh)
            result["deploy"] = deploy
        else:
            time = None
        if waiting:
            result["status"] = "held"
            result["reason"] = "; ".join(p["reason"] for p in waiting)
        elif time is None:
            result["status"] = "held"
            result["reason"] = held_reason(production, result["last_change"], today)
        else:
            result.update(status="dated", date=time[:10], time=time)
    except NotFound as e:
        result.update(status="not_found", date=None, time=None, reason=str(e))
    except Exception as e:
        e.result = result  # what was found before it failed, for the command line to print
        raise
    return result


def contains(repo, sha, head, gh):
    """`compare`'s status if `head` contains `sha` (ahead or identical), else None."""
    status = read(gh, f"repos/{repo}/compare/{quote(sha, safe='/')}...{quote(head, safe='/')}",
                  f"whether {head} contains {sha}")["status"]
    return status if status in ("ahead", "identical") else None


def by_workflow(repo, default, workflow, last, today, gh):
    """The first successful run on the default branch or a tag whose commit contains the
    landing commit, searched in day windows from the day before it landed to `today`."""
    try:
        gh(f"repos/{repo}/actions/workflows/{workflow}")
    except GhError as e:
        kind = failure_kind(e)
        if kind == "not found":
            raise NotFound(f"the workflow `{workflow}` isn't there ({e}); check `production`'s workflow")
        raise NotFound(f"gh couldn't read the workflow `{workflow}`: {kind or 'an error'} ({e})")
    tags = {}

    def tag_commit(name):
        """The commit tag `name` points to, or None when there's no such tag."""
        if name not in tags:
            try:
                obj = gh(f"repos/{repo}/git/ref/tags/{quote(name, safe='/')}")["object"]
            except GhError as e:
                if "404" not in str(e):
                    raise NotFound(f"gh couldn't read whether `{name}` is a tag: {e}")
                obj = None
            # An annotated tag can point at another annotated tag: follow them to the commit.
            for _ in range(MAX_STACK):
                if not obj or obj["type"] != "tag":
                    break
                obj = read(gh, f"repos/{repo}/git/tags/{obj['sha']}", f"the tag `{name}`")["object"]
            if obj and obj["type"] == "tag":
                raise NotFound(f"the tag `{name}` points through more than {MAX_STACK} tags")
            tags[name] = obj["sha"] if obj else None
        return tags[name]

    def deploys(run):
        """Whether the run may have deployed: it succeeded, or it was re-run (GitHub reports a
        run's conclusion from its latest attempt, so an earlier attempt may have succeeded)."""
        if run["conclusion"] != "success" and run["run_attempt"] < 2:
            return False
        if run["event"] in ("pull_request", "pull_request_target"):
            return False
        # A run on a tag has the tag as its branch; a branch can share a tag's name, so the
        # run must be of the tag's own commit.
        branch = run["head_branch"]
        return bool(branch) and (branch == default or tag_commit(branch) == run["head_sha"])

    one_day = datetime.timedelta(days=1)
    start = utc_day(last["landed_at"]) - one_day
    deployed_before = False
    best = None  # (finished at, deploy) of the earliest-finishing run that contains it
    while start <= today and not (best and best[0][:10] < start.isoformat()):
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
            deployed_before = deployed_before or run["conclusion"] == "success"
            # A run that started after the best one finished can't have finished first.
            if best and run["created_at"] > best[0]:
                break
            status = contains(repo, last["landing_sha"], run["head_sha"], gh)
            if not status:
                continue
            # Dated by its first successful attempt: a run can succeed only on a re-run, after a
            # later run, so the scan goes on until no later run could have finished sooner.
            attempt, finished = first_success(repo, run, gh)
            if attempt is None:
                continue
            if not best or finished < best[0]:
                best = (finished, {"kind": "workflow", "workflow": workflow, "run_id": run["id"],
                                   "url": run["html_url"], "head_sha": run["head_sha"],
                                   "head_branch": run["head_branch"], "event": run["event"], "attempt": attempt,
                                   "matched": f"compare {last['landing_sha']}...{run['head_sha']}: {status}"})
        start = end + one_day
    if best:
        return best[1], best[0]
    if deployed_before or ever_deployed(repo, workflow, deploys, gh):
        return None, None
    raise NotFound(f"no successful `{workflow}` runs on the default branch or a tag; check `production`'s workflow")


def list_runs(repo, workflow, created, gh):
    """(runs, capped): a workflow's runs, every page; capped when GitHub has more than one
    search returns (it reports the true total_count). All of them, not only successful
    ones: GitHub gives a run its latest attempt's status, so a run that deployed and was
    then re-run is listed as failed, or as queued or in progress while the re-run goes."""
    runs = []
    for body in pages(gh, f"repos/{repo}/actions/workflows/{workflow}/runs?{created.lstrip('&')}",
                      f"`{workflow}`'s runs"):
        if body["total_count"] > SEARCH_LIMIT:
            return runs, True
        runs += body["workflow_runs"]
    return runs, False


def ever_deployed(repo, workflow, deploys, gh):
    """Whether any run, ever, deployed: an attempt succeeded, on the default branch or a tag.
    Listed with no status filter, since a run that deployed and was then re-run and failed is
    listed as failed."""
    total = seen = 0
    for body in pages(gh, f"repos/{repo}/actions/workflows/{workflow}/runs", f"`{workflow}`'s runs"):
        total = body["total_count"]
        seen += len(body["workflow_runs"])
        for run in body["workflow_runs"]:
            if deploys(run) and (run["conclusion"] == "success" or first_success(repo, run, gh)[0]):
                return True
    if seen < total:
        raise NotFound(f"page limit: none of the {seen} `{workflow}` runs GitHub lists deployed, "
                       f"and it lists no more of its {total}")
    return False


def first_success(repo, run, gh):
    """(attempt, finished at) of the run's first successful attempt, or (None, None) when no
    attempt succeeded: a run can succeed only on a re-run, fail on a later one, or finish
    the day after it started."""
    for n in range(1, run["run_attempt"] + 1):
        attempt = read(gh, f"repos/{repo}/actions/runs/{run['id']}/attempts/{n}", f"run {run['id']}'s attempts")
        if attempt["conclusion"] == "success":
            return n, attempt["updated_at"]
    return None, None


def by_release(repo, last, today, gh):
    """The first published release, by publish date, whose tag contains the landing commit.
    The API lists releases by when each was created, so every page is read and sorted here."""
    since = (utc_day(last["landed_at"]) - datetime.timedelta(days=1)).isoformat()
    releases = [r for body in pages(gh, f"repos/{repo}/releases", "the releases") for r in body]
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


def main(argv=None, gh=gh_api):
    args = parse(sys.argv[1:] if argv is None else argv)
    production = ({"workflow": args.workflow} if args.workflow else
                  "release" if args.release else "merge" if args.merge else None)
    today = args.today or datetime.datetime.now(datetime.timezone.utc).date()
    try:
        result, code = find(args.repo, production, args.prs, today, gh), 0
    except Exception as e:  # a bug, or an answer from gh it doesn't understand: say so, never a date
        result = getattr(e, "result", None) or {"repo": args.repo, "production": production, "last_change": None,
                                                "deploy": None, "prs": []}
        result.update(status="not_found", date=None, time=None,
                      reason=f"production_date.py failed ({type(e).__name__}: {e}); "
                             f"date not found until it's fixed, so report it")
        code = 1
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
