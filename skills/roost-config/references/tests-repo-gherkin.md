# Test adapter: Gherkin files in the repo

How tests work when `tests.kind` is `repo-gherkin`: a story's tests are Cucumber scenarios in the team's own `.feature` files, found by the story's tag and run with each repo's `e2e` commands. The tracker can be any kind; there's no test ticket. The skills say *what* to do with a story's tests ("read its scenarios", "mark it automated"); the operations below say *how*, with `.feature` files.

## In a prompt

A prompt that must stand alone (the tech lead prompt) introduces the tests as: "The Cucumber scenarios for each story: those in the repo tagged with its key, and the drafts in its `scenarios:` comment, which you commit first, test-first."

## What it needs

At least one repo with `e2e.scenarios_dir` and `e2e.run_tags` (with `{tags}`); `roost-config` stops without one. Every repo that has both holds scenarios: a story's tests are looked for in each, and each runs in its own repo. `e2e.tag_style` says how a key is written as a tag, and `e2e.backend_marker` how a scenario points at a backend test. `tests.automated_label` and `tests.xray` don't apply.

## Operations

| Operation | With Gherkin files in the repo |
|---|---|
| **A story's tests** | The `.feature` files under each repo's `e2e.scenarios_dir` with a scenario carrying the story's tag ("What a test is"), plus any drafted in the story's `scenarios:` comment and not committed yet. |
| **Read a test's scenarios** | The file's scenarios that carry the story's tag, with its `Background:`. |
| **Find a scenario's automation** | Its step definitions, as a run reports them ("Reading a run"): a scenario with no undefined or pending step, and not skipped on purpose, has automation. A scenario with `e2e.backend_marker` points at a backend test, which is its automation. |
| **Run a test** | `e2e.run_tags` with the story's tag, in the file's repo, on the commit under test ("Running a story's scenarios"). Record every run in the story's `scenarios:` comment, whatever its results. |
| **Mark a test automated** | No label or status: post or edit the story's `scenarios:` comment with each test, each scenario's result and the commit ("The `scenarios:` comment"). |
| **Write scenarios** | Cucumber scenarios in the Gherkin style guide in the `live-verified-bdd` skill. `Feature:` and `Background:` are allowed. Every scenario carries the story's tag, on itself or from its `Feature:` line. |
| **Unmark a test** | A test that passed before and fails now: say so in the `scenarios:` comment, with the failing scenario and the commit, and take it off the line of automated tests. A test that gets a new scenario is unmarked the same way until that scenario passes. |
| **Create a test** | Before the code exists, draft it on the story ("Writing scenarios before the code"). When the code runs, write the file ("Writing scenarios for code that runs"). `create-xray-test` isn't used. |
| **Update a test's scenarios** | Edit the file in the PR. Never change a scenario to make it pass; only when the behaviour deliberately changed, and say why. |
| **Split a test** | "Splitting a test": the scenarios that won't be automated leave the file and the suite, and their checks go into the story's acceptance criteria; every other scenario stays. |
| **Retire a test** | "Retiring a test". |
| **Shared setup** | A `Background:` in the file, or step definitions the files share. Never a ticket. |
| **Manual tests** | Don't exist here yet. A check no scenario can make goes into the story's acceptance criteria, checked on the PR with evidence. |

## What a test is

- **A test is one `.feature` file's scenarios that carry the story's tag,** on the scenario or inherited from `Feature:` (Cucumber also applies tags on `Rule:` and `Examples:`). A file can hold scenarios from several stories; each story's test is its own scenarios in it. There's no test ticket and no test key.
- **The tag is always the story's key,** written as the tracker adapter writes a key in a name ("Keys": `@issue-123` with GitHub, `@PROJ-123` with Jira), in the form `e2e.tag_style` gives. If `e2e.tag_style` says "the test's key", read it as the story's: here, tests have no keys.
- **Match the whole tag, never a prefix,** so `@issue-42` never picks up `@issue-420`. Find the candidate files with a whole-tag search (for example `grep -rlE '(^|[[:space:]])@PROJ-1250([[:space:]]|$)' <e2e.scenarios_dir>`); take the story's scenarios from the run, since Cucumber applies inherited tags and matches whole tags itself.
- **Cross-cutting:** a scenario that needs several stories is tagged with the last story it depends on.
- **A bug with no story** (a standalone bug's regression test) is tagged with the bug's key, and its `scenarios:` comment goes on the bug.

## Running a story's scenarios

Run `e2e.run_tags` with `{tags}` set to the story's tag (`@PROJ-1250`), in the repo that holds the files, on the commit under test. Run it now; don't rely on CI or an earlier run. Several stories at once: `"@PROJ-1250 or @PROJ-1251"`.

## Reading a run

Cucumber reports each scenario as one of these:

| Cucumber says | The scenario is |
|---|---|
| passed | automated and passing |
| undefined (a step has no definition) or pending (a step is marked pending) | not automated: name the step |
| failed | automated and failing: give the first line of the error |
| ambiguous (two step definitions match a step) | automated and failing: name both definitions |
| skipped, with `e2e.backend_marker` | its backend test's result, run by that test's name in its repo; record the backend test's name with the result |
| skipped because its flag tags don't match the local stack's flag state | couldn't run: name the tag and the actual flag value |
| skipped on purpose, with a reason in a comment (a scenario blocked for now) | not automated: give the reason |
| skipped for any other reason | couldn't run: say why if the output does |

A test is automated and passing only when every one of its scenarios is (for a `e2e.backend_marker` scenario, when its backend test passed). A story's tests are automated when they are in every repo that holds them. Never read a result from the exit code alone.

## The `scenarios:` comment

One comment per story, starting `scenarios:`, edited in place, never a second one. Every run goes in it, passing or not: it's the only record of the story's tests, so a run where nothing passed is recorded too. It holds:

- **The drafts,** before they're committed: each file as a heading with its path and repo, and its full text in a code block ("Writing scenarios before the code"). Once a file is committed, its draft leaves the comment; the file is the test.
- **The last run,** one section per repo that holds the story's scenarios: the repo, the commit, the date, and a table with each test (its file), each scenario and its result. Under it, one line saying which tests are automated.

With several repos, a session edits only its own repo's section, and reads the comment again just before editing it.

## Writing scenarios before the code

When an epic is shaped (`shape-epic` phase 5), the code doesn't exist yet, so each test's scenarios are written in full and posted on its story in its `scenarios:` comment: each file's path under the repo's `e2e.scenarios_dir`, and its full `.feature` text, tagged with the story's key. The session that builds the story commits them first, in the story's PR: they should fail (or be undefined) before the change and pass after it, test-first.

## Writing scenarios for code that runs

When a session is in a repo with `e2e.scenarios_dir` (`live-verified-bdd`, a bug fix), it writes the scenarios into a `.feature` file under that folder on its current branch, tagged with the story's key: a new file, or an existing one for the same area. A session in another repo drafts them on the story instead, as above.

## Splitting a test

When the user agrees a split (`verify-slice-tests`), every scenario that will be automated stays in the file. Each scenario that won't be automated is deleted from the file in the story's PR, and its check goes into the story's acceptance criteria, to be checked on the PR with evidence. Add the acceptance criterion first and read it back, then delete the scenario. Never keep a scenario that won't be automated in the file under a tag the runs exclude (`@wip`, `@skip`, `@ignore`): it would look like a test nobody runs. The test is then automated once its remaining scenarios pass, recorded in the `scenarios:` comment.

## Retiring a test

Delete its scenarios in a PR that says why, and say so on the story. Retired tests leave every count.
