# Free Tests First (#72) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The production date for a release note comes from a Python script with free tests that run on every PR, and paid evals run only when someone asks for them or before a release.

**Architecture:** One new script, `skills/release-notes/scripts/production_date.py`, takes over `release-notes` step 3 (and the landing-commit part of step 1). It calls `gh api` and prints one JSON result. `release-notes` and `close-out-epic` run it and use what it prints. The script's tests, `scripts/production-date.test.py` (stdlib `unittest`), replace `gh` with a fake GitHub built from recorded fixtures in `scripts/fixtures/production-date/`, and run in `pr-checks`. `.github/workflows/evals.yml` stops running on every push.

**Tech Stack:** Python 3 standard library (`argparse`, `json`, `subprocess`, `datetime`, `unittest`), `gh api`, GitHub Actions, Markdown skills.

**Spec:** #72 (Problem, Proposal, Scope, Acceptance criteria), the kickoff's decisions below, `skills/release-notes/SKILL.md` step 3 on `main` at `47c5175`.

## Decisions (from the kickoff, Alan's answers to #72's open questions)

1. **Evals run only before a release or when asked.** Never on a PR's push. "Asked" means the `run-evals` label, which runs the PR's affected cases **once**, when it's added (remove it and add it again to re-run), or `gh workflow run Evals`. Before a release: the release PR, reopened, as today. No schedule.
2. **A skill may depend on a script in the plugin.**
3. **New scripts are Python.** Existing Bash scripts stay Bash (converting them is #77).
4. **#56's plan (#70) doesn't change.**

Out of scope (#72): rewriting other skills' logic as scripts; changing what any existing eval case checks.

## Current state

Checked on `main` at `47c5175`.

| Question | Finding |
|---|---|
| Where step 3's logic lives | `skills/release-notes/SKILL.md`, the `production` table in "## 3. When customers could use it", and the landing commit in step 1's last paragraph. |
| The bugs #72 lists, as they stand | `gh run list --limit 1000` returns the newest first and drops the oldest; the skill tells the model to move `<end>` earlier, by hand. `<end>` "starts as today" but the next window's end isn't defined. Releases are paged and sorted by `published_at` in the model's head. The landing commit is followed through stacks in prose. None of it is tested. |
| What else does the same job | `skills/close-out-epic/SKILL.md:68` confirms production with the same rules (`gh run list --workflow <file> --status success`, no `--limit`, so 20 runs) and points to `release-notes` step 1 for the landing commit. |
| Does the installed plugin ship `scripts/` and the skill folders? | Yes: `~/.claude/plugins/cache/roost/roost/1.2.0/` holds the whole repo, `scripts/` included (`ls` of that folder). |
| Can a Cursor skill reach `scripts/`? | `scripts/link-skills.sh:22-37` links each `skills/<name>/` folder into `~/.cursor/skills/<name>`. Repo-root `scripts/` isn't linked. `<link>/../../scripts` resolves to `~/.cursor/scripts` when read as text (it only reaches the checkout when resolved through the symlink, `cd -P`). A script **inside** the skill folder is reached through the same link as `SKILL.md`. So the script goes in `skills/release-notes/scripts/`. |
| `runs?created=` forms | Checked on this repo: `created=2026-10-27` → 13, `created=2026-10-26..2026-10-27` → 60, `created=2026-10-27T18:00:00Z..2026-10-27T20:00:00Z` → 6, `created=>=2026-10-26` → 67. Day ranges are inclusive. |
| Paging | `gh api ".../runs?per_page=2&page=2" -i` gives `Link` with `prev`, `next`, `last`. GitHub's docs ("List workflow runs for a workflow") say a search with `created`, `status`, `branch` or `event` returns at most 1,000 results. |
| Attempts | `gh api repos/R/actions/runs/<id>/attempts/1 --jq '[.conclusion, .updated_at, .run_attempt]'` → `["success","2026-10-27T19:15:34Z",1]`. |
| `compare` | `compare/e9b7c4f...47c5175` → `ahead`, the other way → `behind`. A missing workflow file → HTTP 404. |
| Which credential `claude` uses with both set | code.claude.com/docs/en/authentication, "Authentication precedence": `ANTHROPIC_API_KEY` is 3rd, `CLAUDE_CODE_OAUTH_TOKEN` 5th, and "In non-interactive mode (`-p`), the key is always used when present". So today, with both secrets set, CI bills the API key. The workflow must not pass the key when the token is set. |
| `pr-checks` script tests | `.github/workflows/pr-checks.yml:39-48` run the three `*.test.sh` scripts in `validate-plugin`. |

## The script's contract

```
python3 <release-notes skill folder>/scripts/production_date.py --repo OWNER/NAME
    (--workflow FILE | --release | --merge)    # the repo's `production`; none of them: it has none
    [--today YYYY-MM-DD]                       # the search's end; default today, UTC
    PR [PR ...]                                # the merged PRs for the feature in this repo
```

It prints one JSON object and exits 0, whatever it finds; exit 2 is for bad arguments only.

```json
{
  "repo": "acme/acme-api",
  "production": {"workflow": "deploy-production.yml"},
  "status": "dated",
  "date": "2026-03-03",
  "time": "2026-03-03T10:12:40Z",
  "reason": null,
  "last_change": {"pr": 820, "landing_pr": 820, "landing_sha": "c820…", "landed_at": "2026-03-02T16:00:00Z"},
  "deploy": {"kind": "workflow", "workflow": "deploy-production.yml", "run_id": 3003, "url": "https://github.com/…/runs/3003",
             "head_sha": "c821…", "head_branch": "main", "event": "push", "attempt": 1,
             "matched": "compare c820…...c821…: ahead"},
  "prs": [{"pr": 812, "base": "main", "landing_pr": 812, "landing_sha": "…", "landed_at": "…"},
          {"pr": 820, "base": "main", "landing_pr": 820, "landing_sha": "…", "landed_at": "…"}]
}
```

- `status`: `dated` (date and time set); `held` (production hasn't carried it yet: no deploy or release contains it, or a PR hasn't reached the default branch); `not_found` (the date can't be known: no `production`, `gh` can't read something, a page limit, a workflow that has never deployed). `reason` says why for `held` and `not_found`, in a line the skill can put in its checks as it is.
- `deploy.kind`: `workflow` (`run_id`, `url`, `head_sha`, `head_branch`, `event`, `attempt`, `matched`), `release` (`tag`, `url`, `published_at`, `matched`) or `merge` (`pr`, `merged_at`).
- `prs[]` entries for a PR that hasn't landed: `{"pr": 45, "base": "slice-2", "landed": false, "reason": "…"}`.
- `time` is UTC. The note's date is `date` (UTC); the skill formats it.

Rules it keeps from step 3, unchanged: match by commit (`compare` `ahead` or `identical`), never by date; a run counts only if it succeeded and ran on the default branch or a tag, not a pull request; date a run by its first successful attempt's `updated_at`; search from the day before the change landed; releases skip drafts and pre-releases and are checked in `published_at` order; `merge` is the landing PR's `merged_at`; no `production` is "date not found"; a workflow that has deployed before but not this change is `held`; one that has never succeeded is `not_found`.

What changes (each fixes a bug #72 lists): runs are listed with `gh api` page by page, in day windows from the landing day to `--today`; a window that hits the 1,000-result limit is halved until it doesn't (one day still over the limit is `not_found`, "page limit"); each window's end is defined; releases are read in full and sorted in code; the landing commit is followed through stacked branches in code.

---

### Task 1: The plan

**Files:** Create: `docs/plans/2026-10-27-issue-72-free-tests.md`

- [ ] Commit this plan as the branch's first commit: `docs(#72): plan for free tests first`.

### Task 2: Landing commits, `merge` and a missing `production`

**Goal:** The script finds each PR's landing commit (following stacked branches), picks the last change, and dates `merge` and the missing case.

**Files:**
- Create: `skills/release-notes/scripts/production_date.py`
- Create: `scripts/production-date.test.py`, `scripts/fixtures/production-date/stacked.json`, `scripts/fixtures/production-date/one-epic.json`
- Modify: `.github/workflows/pr-checks.yml` (a step that runs the tests)

**Test design.** `FakeGitHub(fixture)` answers the script's `gh_api(path)` calls the way GitHub does: pulls by number, `pulls?state=closed&head=OWNER:BRANCH`, workflow runs filtered by `created` (day or day range) and `status`, 100 a page, 1,000 at most per search with the true `total_count`, attempts, releases newest-created first, 100 a page, `git/ref/tags/<name>`, and `compare` from a commit graph (`parents`). A path it doesn't know raises the same error `gh` gives (`GhError("HTTP 404")`). Fixture objects use the field names `gh api` returned above. Volume (more runs than a page, than 1,000) is generated in the test.

**Acceptance Criteria:**
- [ ] A PR merged into `main` lands as itself.
- [ ] A PR merged into a stack branch lands with the first PR from that branch merged after it, followed until one reaches the default branch; the last change is the latest *landing*, not the latest merge.
- [ ] A PR whose branch never reached the default branch: `held`, named in `prs[]` with `landed: false`.
- [ ] `--merge`: `dated` by the landing PR's `merged_at`.
- [ ] No `production`: `not_found`, "`<repo>` has no `production` in the config", with `last_change` filled in.
- [ ] `gh` can't read a PR: `not_found` with `gh`'s error in `reason`.

**Verify:** `python3 scripts/production-date.test.py` → `OK`

- [ ] Write the tests; run them; see them fail (no module).
- [ ] Write the script's argument parsing, `gh_api`, landing, `merge` and missing; run; see them pass.
- [ ] Add `Test the production-date script: python3 scripts/production-date.test.py` to `validate-plugin` in `pr-checks.yml`.
- [ ] Commit `test(#72): production-date script finds landing commits` … then the script: `feat(#72): …`. Review the task's commits (`/code-review` or a fresh reviewer); fix real findings test-first.

### Task 3: `workflow`

**Goal:** Date a change by the first successful deploy run on the default branch or a tag that contains it.

**Files:** Modify: `skills/release-notes/scripts/production_date.py`, `scripts/production-date.test.py`; create fixtures `workflow-*.json` as needed.

**Acceptance Criteria (tests):**
- [ ] The first deploy that contains the landing commit wins, by `compare`, even when an earlier run on that day doesn't contain it.
- [ ] Failed and cancelled runs, runs on pull requests and on other branches are skipped, even when they contain it; a run on a tag counts.
- [ ] A run that succeeded only on a re-run is dated by that attempt's `updated_at`, not `created_at`.
- [ ] Busy: 250 runs since it landed (more than a page): the oldest containing run is found, on page 3.
- [ ] Busier: 1,500 runs in the window: the window is halved until under the limit; the answer is the same as with no limit. One day with more than 1,000 runs: `not_found`, "page limit".
- [ ] No run contains it, but the workflow has deployed before: `held`. Never succeeded on the default branch or a tag: `not_found`. Workflow file not found: `not_found`.
- [ ] `gh` fails listing runs or reading attempts: `not_found` with the error; never a nearby date.

**Verify:** `python3 scripts/production-date.test.py` → `OK`. Then review, as in Task 2.

### Task 4: `release`

**Goal:** Date a change by the first published release whose tag contains it.

**Acceptance Criteria (tests):**
- [ ] Drafts and pre-releases are skipped, even when they contain it.
- [ ] Releases are checked in `published_at` order: a release created long ago but published after a newer one, beyond the first page (150 releases), is found.
- [ ] Releases published before the day before it landed aren't checked.
- [ ] No release contains it: `held`. Releases can't be read: `not_found`.

**Verify:** `python3 scripts/production-date.test.py` → `OK`. Then review.

### Task 5: `release-notes` and `close-out-epic` run the script

**Files:** Modify: `skills/release-notes/SKILL.md` (step 1's landing paragraph, step 3, step 4's "slice not live" reference, step 7's checks), `skills/close-out-epic/SKILL.md:68`, `README.md` ("What each skill needs": Python 3), `skills/roost-config/references/config-schema.md` (`production`'s meaning, if it names the method).

**Acceptance Criteria:**
- [ ] Step 3 says: for each repo, run the script with the repo's `production` and the feature's merged PRs in it, and use its JSON: `dated` → the date; `held` → hold the note (step 4) with its `reason`; `not_found` → "Date not found: <reason>" in the checks and `[date]`. Every `reason` goes in the checks. The deploy rules stay, written as what the script does.
- [ ] The evidence table shows which run, release or merge, its commit and how it was matched (`matched`).
- [ ] Evidence the user gave still counts: when the user gives the deploys and landings, use them; don't run the script for what's given.
- [ ] `close-out-epic` confirms production with the same script (`status: dated`), instead of its own `gh run list`.
- [ ] Without Python or `gh`: say so in the checks, date not found; no fallback to prose arithmetic.
- [ ] Evals: `release-notes` and `close-out-epic` cases, 3 of 3 each, graders unchanged.

### Task 6: Evals only when asked, on a subscription token

**Files:** Modify: `.github/workflows/evals.yml`, `CONTRIBUTING.md` ("Making changes" step 3 and "Evals").

**Acceptance Criteria:**
- [ ] `on.pull_request.types` is `[labeled, reopened]`; the job runs on `labeled` with `run-evals`, on the release PR's `reopened`, and on `workflow_dispatch`. Not on `synchronize`; not on a reopened non-release PR.
- [ ] With `CLAUDE_CODE_OAUTH_TOKEN` set, `ANTHROPIC_API_KEY` isn't in the step's environment (the docs' precedence puts the key first).
- [ ] CONTRIBUTING has a table: which tests run when (every PR: free checks and script tests; asked: evals; release: evals), and why; that a red eval means "look before release"; both credentials and which one wins when both are set, citing the docs.

### Task 7: PR and report

- [ ] Before the push: every script test, `scripts/check-references.py`, `scripts/check-skills.sh`, `claude plugin validate --strict .`.
- [ ] PR `feat(#72): …` against `main`, saying the Cursor finding and any deploy rule changed and why.
- [ ] Report to the orchestrator.
