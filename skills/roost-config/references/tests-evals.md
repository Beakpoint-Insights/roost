# Test adapter: evals

How tests work when `tests.kind` is `evals`: the repo's tests are eval cases for a Claude Code plugin, run with `claude plugin eval` (roost's own tests work this way). The tracker can be any kind; the tests live in the repo. The skills say *what* to do with a story's tests ("read its scenarios", "mark it automated"); the operations below say *how*, with eval cases.

## In a prompt

A prompt that must stand alone (the tech lead prompt) introduces the tests as: "The eval cases for each story: those already in `<tests.evals.dir>/` tagged with its key, and the drafts in its `evals:` comment, which you commit first, test-first."

## Operations

| Operation | With eval cases |
|---|---|
| **A story's tests** | The cases tagged with the story's key, in `tests.evals.repo`, plus any drafted in the story's `evals:` comment and not committed yet ("What a test is"). |
| **Read a test's scenarios** | Its graders: each `graders/*.md` is one scenario, read with the case's `prompt.md`. |
| **Find a scenario's automation** | The case itself: it's automated when its folder is committed on the branch under test. A case drafted on the story but not committed has none ("Not written"). |
| **Run a test** | `tests.evals.run` with the case's name, in `tests.evals.repo`, on the commit under test ("Running a case"). |
| **Mark a test automated** | No label or status: post (or update) the story's `evals:` comment with each case, its result ("3 of 3") and the commit it ran on. |
| **Write scenarios** | An eval case: a `prompt.md` (front matter with `description`, `tags`, `max_turns`, `allowed_tools`, then the prompt) and one `graders/*.md` per check, following the repo's own guide to its evals (for roost, `CONTRIBUTING.md`). |
| **Unmark a test** | A case that passed before and fails now: say so in the story's `evals:` comment, with the failing grader and the commit. |
| **Create a test** | Before the code exists, draft it in full on the story ("Writing cases before the code"); the building session commits it first, test-first. `create-xray-test` isn't used. |
| **Update a test's scenarios** | Edit its graders in the PR. Never edit a grader to make a case pass; only when the behaviour deliberately changed, and say why. |
| **Split a test** | Two cases: the existing one keeps the graders that pass, a new one gets the rest, tagged the same. |
| **Retire a test** | "Retiring a case". |
| **Shared setup** | None: each case's setup is in its own prompt. |
| **Manual tests** | Don't exist here ("Automated, passing, done"). |

## What a test is

- **A test is an eval case:** a folder `<tests.evals.dir>/<case>/` (default `evals/<case>/`) in the repo `tests.evals.repo` (default the lead repo, `planning.lead_repo`). It holds `prompt.md`, with front matter and the prompt, and `graders/*.md`. There's no test ticket in the tracker.
- **Its scenarios are its graders.** Each grader is one check; a run passes when every scored grader passes.
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
