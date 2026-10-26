# Test adapter: evals

How tests work when `tests.kind` is `evals`: the repo's tests are eval cases for a Claude Code plugin, run with `claude plugin eval` (roost's own tests work this way). The tracker can be any kind; the tests live in the repo.

## What a test is

- **A test is an eval case:** a folder `<tests.evals.dir>/<case>/` (default `evals/<case>/`) in the repo `tests.evals.repo` (default the lead repo, `planning.lead_repo`). It holds `prompt.md`, with front matter and the prompt, and `graders/*.md`. There's no test ticket in the tracker.
- **Its checks are its graders.** Each grader is one check; a run passes when every scored grader passes. Where a skill says "scenario", read "grader".
- **Its story is in its tags.** A case's `tags` include the key of the story it tests, written as the tracker adapter writes a key in a tag (see "Keys" in the tracker adapter), plus the skill it exercises, so a PR that changes that skill runs it. A story's tests are the cases tagged with its key: `grep -l "<key tag>" <tests.evals.dir>/*/prompt.md`.
- **Cross-cutting:** a case that needs several stories is tagged with the last story it depends on.

## Running a case

`tests.evals.run` runs one case, with `{case}` in its command (default `claude plugin eval . --no-publish --case {case}`). Run it in `tests.evals.repo`, on the branch under test. Three runs per case is the default; every run must pass. The judges that grade replies get a few verdicts wrong, so a case that fails gets one more try, and fails only if it fails again. Read why from the run's results (each failing grader's verdict and the reply it judged), never from the score alone.

## Automated, passing, done

- **Automated** means the case is committed on the branch and every run passed in a run you did. There's no label and no status to set: the case being in the merged code, and a passing run, is the record. Record each run as a comment on the story starting `evals:`, with each case, its result ("3 of 3") and the commit it ran on.
- **Not written yet** means the case was drafted (on the story; see below) but isn't committed.
- **Manual tests don't exist here:** `tests.manual_label` doesn't apply. A check no case can make goes into the story's acceptance criteria, checked on the PR with evidence.
- **No Preconditions:** a case's setup is in its own prompt.

## Writing cases before the code

When an epic is shaped (`shape-epic` phase 5), the code doesn't exist yet, so cases are written in full and posted on their story, one comment starting `evals:` per story, each case as its name, its `prompt.md` and each grader file, in code blocks. The session that builds the story commits them first, in the story's PR, and they should fail before the change and pass after it: test-first.

## Retiring a case

Delete its folder in a PR that says why, and say so on the story. Retired cases leave every count.

## In each skill

| Skill or step | With `tests.kind: evals` |
|---|---|
| `shape-epic` phase 5 | Plan cases, not Xray tests, and post each story's cases on it as an `evals:` comment ("Writing cases before the code"). `create-xray-test` isn't used. |
| `create-xray-test` | Doesn't apply. Say the team's tests are eval cases in the repo, and use `shape-epic` phase 5 or write the case in a PR. |
| `verify-slice-tests` | Its tests are the cases tagged with STORY's key, in `tests.evals.repo`, on the pushed commit. Run each with `tests.evals.run`. Report each as **Passing** (every run passed), **Failing** (name the grader and why, from the results) or **Not written** (drafted on STORY, not committed). Instead of labelling and closing, post the `evals:` comment. A case with a check that can't pass for a reason the user should decide (it needs a real outside service, say) gets a proposed split into two cases, the same way, and waits for the answer. |
| `automate-xray-tests` | Commit the cases drafted in STORY's `evals:` comment, then make the change until each passes every run. Never edit a grader to make a case pass; only when the behaviour deliberately changed, edit it and say why. |
| `run-slice` step 2 | Send `verify-slice-tests` to the session of `tests.evals.repo`. |
| `slice-handoff` step 4 | Run every case tagged with a story of the epic so far. A case that passed before and fails now gets a Bug, sorted in step 2. |
| `release-qa` | Its no-browser QA runs every case tagged with the epic's stories. |
