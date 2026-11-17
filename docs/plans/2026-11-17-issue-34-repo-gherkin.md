# Gherkin files in the repo as the test tool (#34) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-extended-cc:executing-plans to implement this plan task by task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A team whose Cucumber scenarios live as `.feature` files in its own repo sets `tests.kind: repo-gherkin`, and every roost skill that handles tests reads, runs and records those scenarios through a third tests adapter, with no skill branching on the kind.

**Architecture:** One new adapter, `skills/roost-config/references/tests-repo-gherkin.md`, answers every operation that `tests-xray.md` and `tests-evals.md` answer, using the same operation names. `roost-config` turns the kind on and stops when no repo has `e2e.scenarios_dir` and `e2e.run_tags`. Skill steps whose wording assumes a test is a ticket are reworded in the operations' terms. `setup`, the README and an example config come last.

**Tech Stack:** Markdown skills and references, YAML example configs, eval cases (`claude plugin eval`), and the repo's checks (`scripts/check-references.py`, `scripts/check-skills.sh`, `scripts/eval-cases.test.sh`, `claude plugin validate --strict .`). There's no new script, so there are no new unit tests (see "Tests at every level").

**Spec:** #34 and its stories #138 to #141, with their `evals:` comments; `docs/design/issue-34-repo-gherkin.md` (decisions 1 to 6) and the tech lead prompt `docs/design/issue-34-tech-lead-prompt.md`, both on `issue-34-design-doc` (#137) at `742a6d5`. There's no build guide: each story's description is its slice card.

**Config:** written with roost's own config, `.roost/config.yml` (`team.name: roost`, one repo `roost`, `tracker.kind: github`, `tests.kind: evals`, `vcs.stacking: gh-stack`).

**Status:** waiting for Alan's approval. Nothing is posted on the tracker yet.

---

## Current state (checklist 1)

Everything here was checked on 2026-11-17 against `main` at `2466fd0`, with roost 1.4.0.

### The code

| Claim or question | Checked | Result |
|---|---|---|
| The two adapters' shape | read `tests-xray.md`, `tests-evals.md` | Both have: a one-line intro, `## In a prompt`, `## Operations` (13 rows: A story's tests, Read a test's scenarios, Find a scenario's automation, Run a test, Mark a test automated, Write scenarios, Unmark a test, Create a test, Update a test's scenarios, Split a test, Retire a test, Shared setup, Manual tests), `## What a test is`, then the sections the table names (`tests-evals.md:9-25`, `tests-xray.md:9-25`) |
| `roost-config` supported table, adapter list | `skills/roost-config/SKILL.md:59`, `:74` | True. `:59` lists `repo-gherkin` under "Not yet"; `:74` names only `tests-xray.md` and `tests-evals.md` |
| Where a "keys this kind needs" stop fits | read `skills/roost-config/SKILL.md:55-66` | Section 2 already holds two stops: the "not yet" stop (`:62`) and "Skills the config names must be installed" (`:64`). **There's no check today for the keys a kind needs.** The new stop goes there as a third bold-led paragraph, after `:62` |
| `config-schema.md` `tests` and `e2e` | `:42-49`, `:73` | `:42` says "(`repo-gherkin` and `none` aren't supported yet.)"; `:44` says `manual_label` is "*Optional, for `xray`*"; `:73` lists `e2e`'s sub-keys (`run_all`, `run_tags`, `scenarios_dir`, `tag_style`, `backend_marker`, `secrets_file`, `helpers_hint`) |
| Do the skills go through the adapter's operations? | `grep -rnE "automated_label\|Test issue\|test tickets?\|linked tests\|tests' labels\|unlabelled\|Xray" skills` (excluding the Xray adapter, `create-xray-test` and `automate-xray-tests`) | Yes, except for wording. **No skill names Xray, `automated_label` or a test's status directly** outside `setup:34` (the tests question, expected) and `tracker-jira.md:24` ("A ticket's tests", the Jira tracker's word for Xray links, which `repo-gherkin` teams never use). The wording that assumes a test is a ticket is listed in the next table |
| `verify-slice-tests`' split wording vs decision 5 | `skills/verify-slice-tests/SKILL.md:36`, `:38` | **Doesn't fit.** `:36`: "the existing test keeps every automated scenario … and a new test gets the part that isn't automated." `:38`: "Re-run the existing test, push any change, and mark it automated; the new test isn't marked automated." With decision 5 there is no new test. The adapter's "Split a test" can't override a step that names the result; the step is reworded to defer to the operation (Task 1.5) |
| Which skills call "Create a test" | `grep -rn -e 'Split a test' -e 'Create a test' skills` | `release-qa:72`, `run-bug:47`, `bug-bash:39`, `live-verified-bdd:91`, `shape-epic/references/phase-5-tests.md:38`, `shape-epic/SKILL.md:119`. **Three of them (`release-qa`, `run-bug`, `bug-bash`) call it when the code already runs**, so the adapter's "Create a test" must cover that case from slice 1, not only "before the code exists" as the design's table says (Contradictions, C5) |
| Which skills call "Split a test" | same grep | `verify-slice-tests:36`, `:38`, `automate-tests:49` (proposes only; fits as is) |
| `live-verified-bdd`'s hand-off | `skills/live-verified-bdd/SKILL.md:18`, `:89-96` | Already goes through the adapter: "file them as the tests adapter's 'Create a test' says, following its 'Write scenarios' rules". It doesn't pass the repo and branch the session is on, which "Create a test" needs to write the file there |
| `automate-tests` and manual tests | `skills/automate-tests/SKILL.md:12` | Already says "Leave manual tests alone, if the adapter has them". No change needed for #140's "writes no step definitions for a manual scenario" |
| `automate-tests` uses `@skip` for blocked scenarios | `skills/automate-tests/SKILL.md:43` | "mark it skipped in the repo the way its suite does (for example `@skip` in a feature file), with a comment giving the reason". That's "blocked for now", not decision 5's "won't be automated". The run reports it as `skipped`, which decision 3 doesn't sort (Open question 1) |
| The example config's `e2e` | `examples/config.example.yml:60-66` | `tag_style: "the test's key as a tag (@PROJ-1234)"` and `backend_marker: "@backend-automated @skip, with a comment naming the backend test"`. Every new eval case uses this config "but with `tests.kind: repo-gherkin`", so the adapter has to say the tag is always the story's key (Contradictions, C3, C4) |
| How eval cases are picked | `scripts/eval-cases.sh:49-61` | A change under `skills/roost-config/`, to `examples/config.example.yml` or to `.claude-plugin/` runs **every** case; `skills/<name>/` runs the cases tagged `<name>`; another file in `examples/` runs only the cases whose prompt names it |
| Do the new cases' tags pick them up as expected? | the `cases_tagged` regex from `eval-cases.sh:31`, run on each drafted `tags:` line (`grep -qE "[[, ]<skill>[], ]"`) | Yes. `verify-repo-gherkin-scenarios` and `repo-gherkin-needs-e2e` → `roost-config`, `verify-slice-tests`; `repo-gherkin-split-leaves-suite`, `manual-scenario-not-automated` → `verify-slice-tests`; `phase-5-drafts-scenarios`, `no-manual-without-label` → `shape-epic`; `bdd-files-to-repo` → `live-verified-bdd`; `setup-offers-repo-gherkin` → `setup`. `manual-tests` and `issue-13x` tags match no skill folder (`ls skills/manual-tests`: none), which is harmless; the existing `manual-test-not-automated` already carries `manual-tests` |
| What runs on each PR | the above | #138 and #140 change `skills/roost-config/`, so their PRs run every case (about 50 with the new ones). #139 runs `shape-epic` and `live-verified-bdd` cases. #141 runs `setup` cases, plus every case if it edits `examples/config.example.yml` (Open question 4) |
| `check-references.py` and the new text | `scripts/check-references.py:1-60`, `:67-68`, `:92` | Backticked config keys must be in `config-schema.md`; an `e2e` sub-key named in words in the `e2e` row counts (`:49-55`). Backticked file paths under `skills/`, `examples/`, `evals/` must exist. Eval prompts are exempt from path checks (`:92`). So: never write a `tests.repo_gherkin.*` key (there are none), and add `tests-repo-gherkin.md` in the same commit that names it |
| Baseline checks on `main` | `scripts/check-references.py`, `scripts/check-skills.sh`, `scripts/eval-cases.test.sh`, `claude plugin validate --strict .` | All pass ("All references resolve (177 files, 23 skills, 193 config keys)") |
| `CONTRIBUTING.md` evals table | `CONTRIBUTING.md:62-100` | One row per case; the eight new cases each get one |
| `setup`'s tests question and its check | `skills/setup/SKILL.md:27`, `:34`, `:49-62` | `:27` names the two example configs to start from; `:34` offers Xray or eval cases; step 4 (`:49`) reads the config back through `roost-config` and checks each kind ("for eval cases: `tests.evals.dir` exists …"). `repo-gherkin` needs a line in both `:34` and step 4 |
| README support table | `README.md:67` | "Test management … Planned: Gherkin files in the repo" linking #34 |

### Wording that assumes a test is a ticket

| Where | Text today | Story |
|---|---|---|
| `skills/slice-handoff/SKILL.md:36` | "the tests linked to each story in EPIC so far, with their labels and statuses" | #138 |
| `skills/slice-handoff/SKILL.md:83` | "Check NEXT's tests exist, are linked to NEXT, and match …" | #138 (**not in the prompt's list**) |
| `skills/run-slice/SKILL.md:74` | "its linked tests' labels and statuses" | #138 |
| `skills/run-slice/SKILL.md:206` | "may stay open and unlabelled" | #138 |
| `skills/verify-slice-tests/SKILL.md:36`, `:38` | "a new test gets the part that isn't automated"; "the new test isn't marked automated" | #138 (**not in the story's scope list**; its acceptance criterion on splits needs it) |
| `skills/release-qa/SKILL.md:72`, `:75` | "Create a new test … linked to the story, unmarked"; "Link each test to its bug ('relates to')" | #138 (**not in the prompt's list**) |
| `skills/shape-epic/references/phase-5-tests.md:41` | "with that story's Components where tests are tickets" | #139 |
| `skills/shape-epic/references/phase-5-tests.md:50` | "The epic's tests, each linked to a story" | #139 (**not in the prompt's list**) |
| `skills/shape-epic/references/phase-6-guide.md:26`, `:41` | "which test issues should pass"; "Make test pills clickable (link to the ticket)" | #139 |
| `skills/automate-tests/SKILL.md:3` | description: "Automate the tests linked to a story or slice" | Left as is: "linked to a story" reads fine for a tag, and changing a description changes how the skill triggers |
| `skills/run-slice/SKILL.md:31` | example row "2 of 5 tests Done" | Left as is: an example, and evals tests read the same |

### Cucumber's results (the data; checklist 11 has the query)

cucumber-js 11.0.1, run on a scratch suite (not in the repo), reports each scenario as one of **passed, failed, undefined, pending, ambiguous, skipped**. Its summary line separates them: `6 scenarios (1 failed, 1 ambiguous, 1 undefined, 1 pending, 1 skipped, 1 passed)`. Tags on `Feature:` are inherited, and `--tags "@PROJ-1250"` matches the whole tag: a scenario tagged `@PROJ-12500` wasn't run. Decision 3 names four of the six results; `ambiguous` and `skipped` need a rule (Open question 1).

---

## Contracts (checklist 2)

There's no endpoint or schema. The contract has two parts: the adapter's operations, with the same names the skills already call, and the config the adapter reads.

### The config

```yaml
tests:
  kind: repo-gherkin
  manual_label: manual          # optional, from #140: turns manual scenarios on

repos:
  - name: acme-web
    e2e:
      run_all: npm run test:e2e
      run_tags: 'npm run test:e2e -- --tags "{tags}"'
      scenarios_dir: e2e/features/<area>/
      tag_style: "the story's key as a tag (@PROJ-1234)"
      backend_marker: "@backend"  # optional, same meaning as today
```

- **Required:** at least one repo with `e2e.scenarios_dir` and `e2e.run_tags`. Without one, `roost-config` stops and names both keys.
- **Read:** `e2e.scenarios_dir`, `e2e.run_tags`, `e2e.tag_style`, `e2e.backend_marker`, `tests.manual_label`.
- **Ignored:** `tests.automated_label`, `tests.xray.*`, `tests.evals.*`.
- **No new keys.** `config-schema.md` gains no row; only the `kind`, `manual_label` and `e2e` rows' wording changes.

### The adapter's operations

The full text of `tests-repo-gherkin.md` is in Task 1.2 (slice 1) and Task 3.2 (its "Manual tests" section, slice 3). Its table:

| Operation | With Gherkin files in the repo |
|---|---|
| **A story's tests** | The `.feature` files under each repo's `e2e.scenarios_dir` with a scenario carrying the story's tag ("What a test is"), plus any drafted in the story's `scenarios:` comment and not committed yet. |
| **Read a test's scenarios** | The file's scenarios that carry the story's tag, with its `Background:`. |
| **Find a scenario's automation** | Its step definitions, as a run reports them ("Reading a run"). A scenario with no undefined or pending step has automation. A scenario with `e2e.backend_marker` points at a backend test, which is its automation. |
| **Run a test** | `e2e.run_tags` with `{tags}` set to the story's tag, in the file's repo, on the commit under test ("Running a story's scenarios"). |
| **Mark a test automated** | No label or status: post or edit the story's `scenarios:` comment with each test, each scenario's result and the commit ("The `scenarios:` comment"). |
| **Write scenarios** | Cucumber scenarios in the `live-verified-bdd` style guide. `Feature:` and `Background:` are allowed; every scenario carries the story's tag, on itself or from `Feature:`. |
| **Unmark a test** | A test that passed before and fails now: say so in the `scenarios:` comment, with the failing scenario and the commit. |
| **Create a test** | Before the code exists, draft it on the story ("Writing scenarios before the code"). When the code runs, write the file ("Writing scenarios for code that runs"). `create-xray-test` isn't used. |
| **Update a test's scenarios** | Edit the file in the PR. Never change a scenario to make it pass; only when the behaviour deliberately changed, and say why. |
| **Split a test** | The scenarios that pass stay; the rest are deleted from the file in the PR, and each one's check goes into the story's acceptance criteria ("Splitting a test"). |
| **Retire a test** | "Retiring a test". |
| **Shared setup** | A `Background:` in the file, or step definitions the files share. Never a ticket. |
| **Manual tests** | Slice 1: "Don't exist here" (as in `evals`). Slice 3: "Manual tests", when the config has `tests.manual_label`. |

### The `scenarios:` comment (fixed shape)

One comment per story, edited in place, never a second one. Drafts first, results once there's a run:

````markdown
scenarios: PROJ-1250

### `e2e/features/keys/api-keys.feature` (acme-web)

```gherkin
@PROJ-1250
Feature: API keys
  …
```

### Last run: acme-web at `a1b2c3d`, 2026-11-20

| Test | Scenario | Result |
|---|---|---|
| `e2e/features/keys/api-keys.feature` | A new key is listed with its name | Passed |
| `e2e/features/keys/api-keys.feature` | A revoked key shows as revoked | Not automated: "the key is revoked" has no definition |
| `e2e/features/keys/key-rotation.feature` | Rotating a key keeps its name | Failing: expected "prod-key", got "prod-key (2)" |

Automated: none (each test has a scenario that didn't pass).
````

With several repos that hold scenarios, the comment has one "Last run" section per repo. A session edits only its own repo's section, and reads the comment again right before editing it (Hard parts).

---

## Blockers outside the epic (checklist 3)

| Dependency | Status | How the plan goes on |
|---|---|---|
| #17, the evals adapter that moved the skills onto the adapter's operations | Closed, completed (`gh issue view 17`) | Built on |
| #137, the design PR | Open, not draft | Plan on its decisions at `742a6d5`. It merges on its own; nothing in this stack depends on it being merged |

No other dependency.

---

## Rollout (checklist 4)

roost ships through release-please: merging to `main` adds to the next release PR, and Alan merges that. There are no flags, no data and no migrations. Existing `xray` and `evals` teams must see no change in behaviour: every reworded step has to read the same for them (Hard parts, pre-mortem 1).

**One deploy.** All four stories ship together, in the next roost release, so roost never offers `repo-gherkin` in `setup` (#141) before manual scenarios work (#140). The stack merges whole, bottom to top, before the release PR is merged.

| Order | Branch | PR | Deploy | Waits for |
|---|---|---|---|---|
| 0 | `issue-34-repo-gherkin` (this plan) | opened with the plan | Deploy 1 (stack `issue-34-repo-gherkin`); `docs:` only, so it never releases on its own | Alan's approval |
| 1 | `issue-138-roost` | | Deploy 1 | the plan |
| 2 | `issue-139-roost` | | Deploy 1 | #138's adapter ("Create a test", "Write scenarios") |
| 3 | `issue-140-roost` | | Deploy 1 | #138's adapter (its "Manual tests" row) |
| 4 | `issue-141-roost` | | Deploy 1 | #138 to #140: `setup` offers the kind only once everything it promises works |

**Rollout needed: no.** Merging the one stack and releasing it is enough: nothing to migrate, flag or set up elsewhere, and only one deploy.

---

## Rules the skills never break (checklist 5)

roost has no server. The nearest thing, enforced in the skills' text and checked by eval cases:

| Rule | Where it's written | Checked by |
|---|---|---|
| A test is marked automated (the `scenarios:` comment says "Automated") only from a run done now, on a named commit, in which every scenario passed | adapter "Mark a test automated", "Reading a run"; `verify-slice-tests:26`, `:33` | `verify-repo-gherkin-scenarios` (`sorts-by-run`) |
| No label or status is set on any ticket for a test | adapter "Mark a test automated" | `verify-repo-gherkin-scenarios`, `repo-gherkin-split-leaves-suite` (fail if an `automated` label or Done) |
| A manual scenario is closed only by a `manual run:` comment, never by automation | adapter "Manual tests" (#140) | `manual-scenario-not-automated` |
| Guessed `e2e` values are never used as if they were in the config | `roost-config` section 2 stop | `repo-gherkin-needs-e2e` |

---

## Failure visibility (checklist 6)

The failures are what the user is told:

| Failure | What the user sees | Where it's written | Checked by |
|---|---|---|---|
| `repo-gherkin` with no repo that has `e2e.scenarios_dir` and `e2e.run_tags` | A stop naming both keys, with values suggested only from what the user or the repo shows, for them to confirm | `roost-config` section 2 | `repo-gherkin-needs-e2e` |
| A scenario that couldn't run (the suite didn't start, a flag tag that doesn't match the stack's flag state, a skip with no reason) | "Couldn't run" with the reason in one line, never a guessed result | adapter "Reading a run"; `verify-slice-tests:32` | `verify-repo-gherkin-scenarios` covers the other results; this one is read in review |
| A file that mixes manual and automated scenarios | Flagged, with a proposal to move the manual ones into their own file | adapter "Manual tests" (#140) | `manual-scenario-not-automated` (`dns.feature`) |
| A test's tag that only prefixes the story's key (`@PROJ-12500`) | Not counted as the story's | adapter "What a test is" | `verify-repo-gherkin-scenarios` |

---

## Branch sizing and callers (checklist 7)

| Branch | Concern | Changes callers outside its own skill | Size |
|---|---|---|---|
| `issue-138-roost` | The adapter and turning the kind on | **Yes, on purpose.** `roost-config` is loaded by all 23 skills. The adapter is read by every skill that handles tests: `verify-slice-tests`, `automate-tests`, `slice-handoff`, `run-slice`, `release-qa`, `run-bug`, `bug-bash`, `live-verified-bdd`, `shape-epic` phases 5 and 6, `close-out-epic`. The branch rewords wording in four of them: `run-slice:74`, `:206`; `slice-handoff:36`, `:83`; `verify-slice-tests:36`, `:38`; `release-qa:72`, `:75`. They span orchestration, verification and release QA, but it's one concern (a test isn't always a ticket), about a dozen lines plus one new file. One branch, with the callers named in the PR description | 1 new file, about 12 changed lines, 3 eval cases plus 1 (Open question 3) |
| `issue-139-roost` | Writing scenarios before and after the code | `shape-epic` phase 5 (`shape-epic/SKILL.md:119` calls it) and phase 6, and `live-verified-bdd:91`. Within two skills | about 6 changed lines, 2 eval cases |
| `issue-140-roost` | Manual scenarios | The adapter's "Manual tests" section is read by `verify-slice-tests:17`, `:24`, `:33`, `automate-tests:12`, `slice-handoff:41`, `:76`, `run-slice:205`, `build-epic:82`, `close-out-epic`, `phase-5-tests.md:11`. All already go through "Manual tests" and need no change | 1 section, 1 schema row, 2 eval cases |
| `issue-141-roost` | Offering it in setup | `setup`, `README.md`, a new example file. No callers | about 6 changed lines, 1 new file, 1 eval case |

---

## Open questions (checklist 8)

Each has a recommendation; nothing is decided until Alan answers.

1. **The two results decision 3 doesn't name.** Cucumber also reports `ambiguous` (two step definitions match a step) and `skipped`. **Recommend:** `ambiguous` is **failing** (the automation exists but is wrong; name both definitions). `skipped` is never "passed": a `e2e.backend_marker` scenario takes its backend test's result; a scenario skipped because its flag tags don't match the stack's flag state is "Couldn't run" (as `verify-slice-tests:32` already says); a scenario the suite skips on purpose with a reason (`automate-tests:43`'s "blocked" skip) is **not automated**, with the reason from its comment.
2. **"Create a test" when the code already runs.** The design's table covers only "before the code exists", but `release-qa:72`, `run-bug:47` and `bug-bash:39` call "Create a test" when the code runs. **Recommend:** #138's adapter covers both cases (decision 1 already decides the second). The cost: #139's `bdd-files-to-repo` may already pass at #138's head, so #139's test-first run may not fail before its change. #139 records that run, and its own work is the wording in `shape-epic` and `live-verified-bdd`.
3. **Guard the Xray split.** The reworded `verify-slice-tests` steps 7 and 8 are the likeliest place to break Xray teams, and no eval case covers an Xray split today. **Recommend:** #138 adds one case, `xray-split-makes-new-test` (Task 1.1), which checks that with the Xray example config an agreed split still creates a new test with `create-xray-test` and doesn't label it automated.
4. **Where the example lives.** **Recommend:** a separate file, `examples/config.repo-gherkin.yml` (named like `config.github-only.yml`), not a commented block in `examples/config.example.yml`. A separate file keeps the Xray example as it is, and changing it runs only the cases that name it, not every case (`eval-cases.sh:49-50`). `setup:27` names it as a third starting point.
5. **The mixed manual and automated file.** #140 wants it flagged. **Recommend:** write it in the adapter's "Manual tests" only. If `manual-scenario-not-automated`'s grader still fails on `dns.feature`, add one line to `verify-slice-tests` step 2 that reads the same for every adapter ("A test that mixes manual and automated scenarios: flag it and propose separating them"), since Xray's rule is the same (`tests-xray.md:95`).
6. **Several repos with scenarios.** **Recommend:** one `scenarios:` comment per story, with one "Last run" section per repo, each edited only by that repo's session.
7. **Wording outside the stories' lists.** `release-qa:72`, `:75`, `slice-handoff:83` and `phase-5-tests.md:50` also assume a test is a ticket. **Recommend:** fix them in #138 (`release-qa`, `slice-handoff`) and #139 (`phase-5-tests.md`), as the epic's scope allows ("Wording fixes in any skill whose step doesn't fit `.feature` files").

---

## Contradictions (checklist 9)

| # | Contradiction | Resolution |
|---|---|---|
| C1 | #140's description says "The `manual-test-not-automated` eval case gets a `repo-gherkin` variant", but its `evals:` comment and the tech lead prompt draft a new case, `manual-scenario-not-automated` | Follow the `evals:` comment and the prompt: a new case. The existing Xray case is unchanged |
| C2 | #138's criterion says `grep -rn repo-gherkin skills/` finds it only in the adapter, `roost-config` and `config-schema.md`; the prompt's success check adds `setup` | Both hold, at different heads: `setup` names it only from #141. Each story's PR checks its own list |
| C3 | Decision 2: the tag is the **story's** key. The example config's `tag_style` says "the test's key as a tag", and every new eval case uses that config | The adapter says the tag is always the story's key, since there are no test keys; `tag_style` only says how a key is written as a tag. #141's example writes "the story's key" |
| C4 | Decision 5: never park scenarios under `@skip`. The example's `backend_marker` is "`@backend-automated @skip`", and `automate-tests:43` marks blocked scenarios `@skip` | Different things. A backend-marker skip isn't parking: the backend test is its automation. A blocked skip is temporary and reported as not automated (Open question 1). The adapter's "Splitting a test" names only what decision 5 forbids: keeping a scenario that **won't** be automated |
| C5 | The design's "Create a test" covers only "before the code exists"; decision 1 and three callers need "the code already runs" | Open question 2 |
| C6 | "Each should fail before the change and pass after it" (each `evals:` comment). After #138, `no-manual-without-label` (#140) and `phase-5-drafts-scenarios` (#139) may already pass, since the adapter drafts on the story and has no manual tests until #140 | Each story commits its cases first and runs them; a case that already passes is recorded as such in the story's `evals:` comment, not forced to fail |
| C7 | Decision 3 has four results; cucumber-js reports six | Open question 1 |

No contract changes a default the decisions say stays the same: no new keys, and the `xray` and `evals` adapters are untouched.

---

## Hard parts (checklist 10)

| Component | Shared state | Partial failure | Lifetimes | Real data | Cost of seeing it |
|---|---|---|---|---|---|
| The new adapter | The story's `scenarios:` comment. Two sessions (two repos with scenarios, or a re-run while another is running) can edit it at once, and the later edit wins | A run that stops halfway leaves the comment as it was; a re-run edits it in place, so it's safe | The comment records a commit; it's stale after the next push, and `verify-slice-tests` runs again (`:26`: "Don't rely on CI or an earlier run") | Tags on `Feature:`, `Rule:`, `Scenario:` and `Examples:`; area files mixing stories; tags that prefix others (`@issue-42`, `@issue-420`); six results, not four | The comment grows by one row per scenario of one story; small |
| `roost-config`'s supported check and the keys stop | none | n/a: it reads only | n/a | Configs with `e2e` on a repo that has no scenarios, or `run_tags` without `{tags}` | none |
| `verify-slice-tests`' split steps | The `.feature` file and the story's description | **The split has two writes:** the scenario deleted from the file, and its check added to the story's acceptance criteria. If the second fails, the check is lost | n/a | A scenario that's partly automated (some steps checked) | none |
| `shape-epic` phase 5 | The story's `scenarios:` comment, written once while shaping | Posting stops after some stories: the next run sees which stories already have a comment and doesn't post twice | Drafts go stale if the design changes before the build; the building session commits them as drafted and changes them only as "Update a test's scenarios" says | Cross-cutting tests | none |
| `live-verified-bdd`'s filing step | The `.feature` file on the current branch | A file half-written is visible in `git status` before commit | n/a | A session in a repo with no `e2e.scenarios_dir` (it drafts on the story instead) | none |
| `setup`'s tests question | none | Saves nothing until the user agrees (`setup:12`) | n/a | `cucumber.js`, `cucumber.yml`, `cucumber.json`, `package.json` scripts, or none | none |
| Reworded shared steps (`run-slice`, `slice-handoff`, `release-qa`, `verify-slice-tests`) | Read by every team | n/a | n/a | Xray teams, eval teams | none |

### Pre-mortem: "This shipped and caused an incident. What was it?"

| # | Incident | Rule | Test that proves it | Branch |
|---|---|---|---|---|
| 1 | An Xray team agreed a split and roost deleted the scenario from Xray instead of creating a new test, because the reworded step 7 read like decision 5 | `verify-slice-tests` steps 7 and 8 defer to "Split a test" and name no result of their own; `tests-xray.md` is unchanged | `xray-split-makes-new-test` (new) passes; `verify-not-automate`, `manual-test-not-automated`, `verify-with-eval-cases` still pass | `issue-138-roost` |
| 2 | `verify-slice-tests` counted `@PROJ-12500`'s scenario as PROJ-1250's | Find files by whole tag (`(^|[[:space:]])@KEY([[:space:]]|$)`); take the story's scenarios from the run, which matches whole tags | `verify-repo-gherkin-scenarios` ("Rotation is audited" left out) | `issue-138-roost` |
| 3 | A manual scenario showed as "not automated" on every run, and someone wrote step definitions for it | The run always excludes the manual tag (`{tags}` = `@KEY and not @<manual_label>`), whatever the team's command does | `manual-scenario-not-automated` | `issue-140-roost` |
| 4 | A split deleted a scenario and its check never reached the acceptance criteria | Write the acceptance criterion first, read it back, then delete the scenario; `verify-slice-tests` step 9 reads both back | `repo-gherkin-split-leaves-suite` (both changes named) | `issue-138-roost` |
| 5 | Two repos' sessions overwrote each other's results in the `scenarios:` comment | One "Last run" section per repo; read the comment again right before editing; edit only your repo's section | Read in review (no eval case can run two sessions) | `issue-138-roost` |
| 6 | A blocked `@skip` scenario was reported as passing because Cucumber exits 0 | A skipped scenario is never "passed" (Open question 1) | `verify-repo-gherkin-scenarios` covers passed, undefined and failed; skipped is read in review | `issue-138-roost` |

---

## Data assumptions (checklist 11)

There's no stored data. The "data" is how teams' Cucumber suites and Cucumber's reports look.

| Assumption | Query | Result |
|---|---|---|
| Cucumber reports undefined and pending separately from failed | In the scratchpad, `npm i -D @cucumber/cucumber@11.0.1`, a two-file suite, then `npx cucumber-js --tags '@PROJ-1250 and not @manual' --format summary` | `6 scenarios (1 failed, 1 ambiguous, 1 undefined, 1 pending, 1 skipped, 1 passed)`. **Confirmed for cucumber-js 11.0.1.** Not checked for Cucumber-JVM, Cucumber-Ruby or other flavours; their documentation describes the same results, but nobody ran them here |
| A tag on `Feature:` is inherited by its scenarios | same run | All four scenarios of a file tagged `@PROJ-1250` on `Feature:` ran. Confirmed |
| A tag expression matches whole tags, not prefixes | same run, with a scenario tagged `@PROJ-12500` | Not run. Confirmed |
| `--dry-run` finds undefined steps without running | `npx cucumber-js --dry-run --tags '@PROJ-1250' --format summary` | `7 scenarios (1 ambiguous, 2 undefined, 4 skipped)`: it finds undefined and ambiguous, but reports every defined step as skipped, so it can't tell passing from failing. That supports decision 3's choice of a real run over a dry run |
| Scenarios not excluded by tag run, including manual ones | the dry run above, without `not @manual` | The manual scenario counted (its steps undefined). So the adapter must add `and not @<manual_label>` itself |
| Teams keep area files with several stories' scenarios | none: no team's suite was read | Unchecked. Decision 2 handles it either way (per-scenario tags) |

No query for Alan to run.

---

## Tests at every level

- **Unit tests:** none. No script or logic changes; every change is skill prose, an example config or eval cases. If Open question 1's answer adds no script, that stays true.
- **Repo checks, every task:** `scripts/check-references.py`, `scripts/check-skills.sh`, `scripts/eval-cases.test.sh`, `claude plugin validate --strict .`. All four run in `pr-checks`.
- **Eval cases:** each story's cases, committed first, run with `tests.evals.run` (`claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --case <case>`), 3 of 3 before the PR is ready. On each PR, the `run-evals` label runs what `scripts/eval-cases.sh` picks (every case for #138 and #140).
- **On the PR, not by an eval case:** the success grep (`grep -rn repo-gherkin skills/`), and on #141, the example config loading in `roost-config`.

### How each scenario is checked

| Story | Case | Grader | Checked by |
|---|---|---|---|
| #138 | `verify-repo-gherkin-scenarios` | `sorts-by-run` | that case |
| #138 | `verify-repo-gherkin-scenarios` | `uses-verify` (tool_used) | that case |
| #138 | `repo-gherkin-needs-e2e` | `names-missing-keys` | that case |
| #138 | `repo-gherkin-split-leaves-suite` | `leaves-suite` | that case |
| #138 | `xray-split-makes-new-test` (Open question 3) | `makes-new-test` | that case |
| #138 | acceptance criterion: `grep -rn repo-gherkin skills/` only in the adapter, `roost-config`, `config-schema.md` | | the PR, Task 1.7 |
| #139 | `phase-5-drafts-scenarios` | `drafts-on-stories` | that case |
| #139 | `phase-5-drafts-scenarios` | `no-xray-filing` (tool_used, max 0) | that case |
| #139 | `bdd-files-to-repo` | `files-to-repo` | that case |
| #139 | `bdd-files-to-repo` | `no-xray-filing` (tool_used, max 0) | that case |
| #139 | acceptance criterion: Xray and evals behaviour of these steps unchanged | | the existing `shape-epic` and `live-verified-bdd` cases (`shape-epic-starts-with-problem`, `design-without-ui-is-architecture`, `prototype-stops-without-design-system`, `bdd-for-existing-feature`) still pass |
| #140 | `manual-scenario-not-automated` | `manual-by-record` | that case |
| #140 | `manual-scenario-not-automated` | `no-automate-skill` (tool_used, max 0) | that case |
| #140 | `no-manual-without-label` | `no-manual-scenario` | that case |
| #140 | acceptance criterion: `automate-tests` writes no step definitions for a manual scenario | | `no-automate-skill`, and `automate-tests:12` (unchanged) |
| #141 | `setup-offers-repo-gherkin` | `offers-repo-gherkin` | that case |
| #141 | `setup-offers-repo-gherkin` | `uses-setup` (tool_used) | that case |
| #141 | acceptance criterion: the example config loads in `roost-config` | | the PR, Task 4.4 |
| #141 | acceptance criterion: README no longer lists it as not supported, and links the adapter | | the PR, Task 4.3 (`check-references.py` checks the link) |

No test is manual: roost's config has no `tests.manual_label`.

---

## File structure

| File | Story | Responsibility |
|---|---|---|
| `skills/roost-config/references/tests-repo-gherkin.md` (new) | #138, #140 | The adapter: every operation for `.feature` files |
| `skills/roost-config/SKILL.md` | #138 | Supported table, keys stop, adapter list |
| `skills/roost-config/references/config-schema.md` | #138, #140 | `tests.kind`, `manual_label`, `e2e` wording |
| `skills/verify-slice-tests/SKILL.md` | #138 | Split steps 7 and 8 defer to "Split a test" |
| `skills/run-slice/SKILL.md`, `skills/slice-handoff/SKILL.md`, `skills/release-qa/SKILL.md` | #138 | Wording in the operations' terms |
| `skills/shape-epic/references/phase-5-tests.md`, `phase-6-guide.md` | #139 | Wording in the operations' terms |
| `skills/live-verified-bdd/SKILL.md` | #139 | Hand-off passes the repo and branch |
| `skills/setup/SKILL.md` | #141 | Tests question, starting example, step 4 check |
| `README.md` | #141 | Support table |
| `examples/config.repo-gherkin.yml` (new) | #141 | A `repo-gherkin` team's config |
| `evals/<case>/` (8 new, 9 with Open question 3) | each story | The stories' tests |
| `CONTRIBUTING.md` | each story | One evals-table row per new case |

---

## Story #138: Verify a story's scenarios in the repo (branch `issue-138-roost`, stacked on `issue-34-repo-gherkin`)

### Task 1.1: The eval cases, test-first

**Goal:** #138's cases are committed and fail on the current code.

**Files:**
- Create: `evals/verify-repo-gherkin-scenarios/prompt.md`, `graders/sorts-by-run.md`, `graders/uses-verify.md`
- Create: `evals/repo-gherkin-needs-e2e/prompt.md`, `graders/names-missing-keys.md`
- Create: `evals/repo-gherkin-split-leaves-suite/prompt.md`, `graders/leaves-suite.md`
- Create (Open question 3): `evals/xray-split-makes-new-test/prompt.md`, `graders/makes-new-test.md`
- Modify: `CONTRIBUTING.md` (evals table, after the `verify-with-eval-cases` row)

**Acceptance Criteria:**
- [ ] The three drafted cases are committed word for word from #138's `evals:` comment.
- [ ] Each fails on `main`'s skills (they say `repo-gherkin` isn't supported).
- [ ] `CONTRIBUTING.md` has a row for each.

**Verify:** `scripts/check-references.py && scripts/eval-cases.test.sh` → pass; each case → FAIL

**Steps:**

- [ ] **Step 1: Copy the drafts.** Copy each file from #138's `evals:` comment (`gh issue view 138 -R Beakpoint-Insights/roost --comments`) into the paths above, exactly as drafted.

- [ ] **Step 2: Write the Xray split case** (only if Open question 3 is approved).

`evals/xray-split-makes-new-test/prompt.md`:

````markdown
---
description: With Xray, an agreed split still keeps the automated scenarios on the existing test and puts the rest on a new test created with create-xray-test, unlabelled, instead of deleting them.
tags: [verify-slice-tests, issue-138]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`. You can't reach Jira or Xray from here, so say exactly what you'd change.

We're using verify-slice-tests for story PROJ-1250. Its test PROJ-1251 "API keys" has three scenarios. Two are automated in `e2e/features/keys/api-keys.feature` and passed just now. The third, "The key's secret is emailed to its owner", has no automation: nothing in our e2e suite can read email, and we've agreed it won't be automated. You proposed splitting it, and I agree: go ahead with the split.
````

`evals/xray-split-makes-new-test/graders/makes-new-test.md`:

````markdown
---
type: llm
---

With Xray, a split keeps the automated scenarios on the existing test and moves the rest to a new test.

It passes when the reply:
- keeps the two automated scenarios on PROJ-1251, saving its current scenarios to a local file first, then marks PROJ-1251 automated (the `automated` label, Done);
- creates a new Xray test for "The key's secret is emailed to its owner" with `create-xray-test`, linked to PROJ-1250, with the same Components, moved to Done without the `automated` label.

It fails if it deletes that scenario without creating a new test, moves it only into the story's acceptance criteria, or labels the new test automated.
````

- [ ] **Step 3: Add the rows** to `CONTRIBUTING.md`'s evals table:

```markdown
| `verify-repo-gherkin-scenarios` | With `tests.kind: repo-gherkin`, `verify-slice-tests` finds a story's scenarios by whole tag, sorts them by their run (passed, undefined, failed), and records the result in a `scenarios:` comment with no label or status |
| `repo-gherkin-needs-e2e` | With `repo-gherkin` and no repo with `e2e.scenarios_dir` and `e2e.run_tags`, `roost-config` stops and names both keys instead of guessing them |
| `repo-gherkin-split-leaves-suite` | With `repo-gherkin`, an agreed split deletes the scenarios that won't be automated and moves each one's check into the story's acceptance criteria, instead of parking them under a skip tag |
| `xray-split-makes-new-test` | With Xray, an agreed split still puts the scenarios that won't be automated on a new, unlabelled test made with `create-xray-test` |
```

- [ ] **Step 4: Run the checks and the cases; each case should fail.**

```bash
scripts/check-references.py && scripts/check-skills.sh && scripts/eval-cases.test.sh && claude plugin validate --strict .
for c in verify-repo-gherkin-scenarios repo-gherkin-needs-e2e repo-gherkin-split-leaves-suite xray-split-makes-new-test; do
  claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --case "$c"
done
```

Expected: checks pass. The three `repo-gherkin` cases fail (the reply says `repo-gherkin` isn't supported). `xray-split-makes-new-test` **passes** already: it guards existing behaviour, and must still pass after Task 1.5.

- [ ] **Step 5: Commit**

```bash
git add evals/verify-repo-gherkin-scenarios evals/repo-gherkin-needs-e2e evals/repo-gherkin-split-leaves-suite evals/xray-split-makes-new-test CONTRIBUTING.md
git commit -m "test(#138): eval cases for verifying scenarios in the repo"
```

### Task 1.2: The adapter

**Goal:** `tests-repo-gherkin.md` answers every operation (decisions 1 to 3, 5, 6), with no manual tests yet.

**Files:**
- Create: `skills/roost-config/references/tests-repo-gherkin.md`

**Acceptance Criteria:**
- [ ] It has the same sections as `tests-evals.md`: intro, "In a prompt", "Operations" (13 rows, same names), "What a test is", and each section the table names.
- [ ] Finding is by whole tag; the scenarios are taken from the run.
- [ ] Results follow decision 3, plus Open question 1's answer.
- [ ] "Create a test" covers both "before the code exists" and "the code runs" (Open question 2).
- [ ] "Manual tests": don't exist yet.

**Verify:** `scripts/check-references.py` → pass

**Steps:**

- [ ] **Step 1: Write the file.** Use this text, changed only where Alan's answers to Open questions 1, 2 and 6 differ from the recommendation:

````markdown
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
| **Find a scenario's automation** | Its step definitions, as a run reports them ("Reading a run"): a scenario with no undefined or pending step has automation. A scenario with `e2e.backend_marker` points at a backend test, which is its automation. |
| **Run a test** | `e2e.run_tags` with the story's tag, in the file's repo, on the commit under test ("Running a story's scenarios"). |
| **Mark a test automated** | No label or status: post or edit the story's `scenarios:` comment with each test, each scenario's result and the commit ("The `scenarios:` comment"). |
| **Write scenarios** | Cucumber scenarios in the Gherkin style guide in the `live-verified-bdd` skill. `Feature:` and `Background:` are allowed. Every scenario carries the story's tag, on itself or from its `Feature:` line. |
| **Unmark a test** | A test that passed before and fails now: say so in the `scenarios:` comment, with the failing scenario and the commit. |
| **Create a test** | Before the code exists, draft it on the story ("Writing scenarios before the code"). When the code runs, write the file ("Writing scenarios for code that runs"). `create-xray-test` isn't used. |
| **Update a test's scenarios** | Edit the file in the PR. Never change a scenario to make it pass; only when the behaviour deliberately changed, and say why. |
| **Split a test** | "Splitting a test": the scenarios that pass stay, and the rest leave the file and the suite. |
| **Retire a test** | "Retiring a test". |
| **Shared setup** | A `Background:` in the file, or step definitions the files share. Never a ticket. |
| **Manual tests** | Don't exist here yet. A check no scenario can make goes into the story's acceptance criteria, checked on the PR with evidence. |

## What a test is

- **A test is one `.feature` file's scenarios that carry the story's tag,** on the scenario or inherited from `Feature:` (Cucumber also applies tags on `Rule:` and `Examples:`). A file can hold scenarios from several stories; each story's test is its own scenarios in it. There's no test ticket and no test key.
- **The tag is always the story's key,** written as the tracker adapter writes a key in a name ("Keys": `@issue-123` with GitHub, `@PROJ-123` with Jira), in the form `e2e.tag_style` gives. If `e2e.tag_style` says "the test's key", read it as the story's: here, tests have no keys.
- **Match the whole tag, never a prefix,** so `@issue-42` never picks up `@issue-420`. Find the files with a whole-tag search (for example `grep -rlE '(^|[[:space:]])@PROJ-1250([[:space:]]|$)' <e2e.scenarios_dir>`); take the story's scenarios from the run, since Cucumber applies inherited tags and matches whole tags itself.
- **Cross-cutting:** a scenario that needs several stories is tagged with the last story it depends on.

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
| skipped, with `e2e.backend_marker` | its backend test's result, run by that test's name in its repo |
| skipped because its flag tags don't match the local stack's flag state | couldn't run: name the tag and the actual flag value |
| skipped on purpose, with a reason in a comment (a scenario blocked for now) | not automated: give the reason |
| skipped for any other reason | couldn't run: say why if the output does |

A test is automated and passing only when every one of its scenarios is. Never read a result from the exit code alone.

## The `scenarios:` comment

One comment per story, starting `scenarios:`, edited in place, never a second one. It holds:

- **The drafts,** before they're committed: each file as a heading with its path and repo, and its full text in a code block ("Writing scenarios before the code").
- **The last run,** one section per repo that holds the story's scenarios: the repo, the commit, the date, and a table with each test (its file), each scenario and its result. Under it, one line saying which tests are automated.

With several repos, a session edits only its own repo's section, and reads the comment again just before editing it.

## Writing scenarios before the code

When an epic is shaped (`shape-epic` phase 5), the code doesn't exist yet, so each test's scenarios are written in full and posted on its story in its `scenarios:` comment: each file's path under the repo's `e2e.scenarios_dir`, and its full `.feature` text, tagged with the story's key. The session that builds the story commits them first, in the story's PR: they should fail (or be undefined) before the change and pass after it, test-first.

## Writing scenarios for code that runs

When a session is in a repo with `e2e.scenarios_dir` (`live-verified-bdd`, a bug fix), it writes the scenarios into a `.feature` file under that folder on its current branch, tagged with the story's key: a new file, or an existing one for the same area. A session in another repo drafts them on the story instead, as above.

## Splitting a test

When the user agrees a split (`verify-slice-tests`), the scenarios that pass stay in the file. Each scenario that won't be automated is deleted from the file in the story's PR, and its check goes into the story's acceptance criteria, to be checked on the PR with evidence. Add the acceptance criterion first and read it back, then delete the scenario. Never keep a scenario that won't be automated in the file under a tag the runs exclude (`@wip`, `@skip`, `@ignore`): it would look like a test nobody runs. The test is then automated once its remaining scenarios pass, recorded in the `scenarios:` comment.

## Retiring a test

Delete its scenarios in a PR that says why, and say so on the story. Retired tests leave every count.
````

- [ ] **Step 2: Check it and commit**

```bash
scripts/check-references.py
git add skills/roost-config/references/tests-repo-gherkin.md
git commit -m "feat(#138): a tests adapter for Gherkin files in the repo"
```

Expected: "All references resolve". The commit message is `feat` so release-please lists it.

### Task 1.3: Turn the kind on in `roost-config`

**Goal:** `repo-gherkin` is supported, its adapter is named, and a config without the `e2e` keys stops.

**Files:**
- Modify: `skills/roost-config/SKILL.md:59`, after `:62`, `:74`
- Modify: `skills/roost-config/references/config-schema.md:42`, `:73`

**Acceptance Criteria:**
- [ ] `tests.kind` row: supported `xray`, `evals`, `repo-gherkin`; not yet `none`.
- [ ] A new stop, in section 2's style, names both `e2e` keys.
- [ ] The schema's `kind` and `e2e` rows say what `repo-gherkin` reads.

**Verify:** `scripts/check-references.py && claude plugin validate --strict .` → pass

**Steps:**

- [ ] **Step 1: `SKILL.md:59`**

```markdown
| `tests.kind` | `xray`, `evals`, `repo-gherkin` | `none` |
```

- [ ] **Step 2: After `SKILL.md:62`,** add:

```markdown
**Keys a tests kind needs.** With `tests.kind: repo-gherkin`, at least one repo needs both `e2e.scenarios_dir` and `e2e.run_tags`. If none has them, stop and say so, naming both keys. Suggest values only from what the user or the repo shows (a Cucumber config, a test script), for them to confirm; never go on with guessed values as if they were in the config.
```

- [ ] **Step 3: `SKILL.md:74`**

```markdown
- The tests adapter for `tests.kind`, before touching tests: `tests-xray.md` (Xray tests and their Cucumber scenarios), `tests-evals.md` (eval cases in the repo), or `tests-repo-gherkin.md` (Cucumber scenarios in the repo's own `.feature` files). Each says what a test is, and its operations ("A story's tests", "Read a test's scenarios", "Run a test", "Mark a test automated", "Create a test", …) say how to do each thing the skills ask, with this team's tests.
```

- [ ] **Step 4: `config-schema.md:42`**

```markdown
| `kind` | `xray`: Xray tests in Jira, with Cucumber scenarios. `evals`: eval cases in a plugin's repo, run with `claude plugin eval` (see `tests-evals.md`). `repo-gherkin`: Cucumber scenarios in the repo's own `.feature` files, found by the story's tag and run with each repo's `e2e` commands (see `tests-repo-gherkin.md`); needs a repo with `e2e.scenarios_dir` and `e2e.run_tags`. (`none` isn't supported yet.) |
```

- [ ] **Step 5: `config-schema.md:73`,** append to the `e2e` row's meaning:

```markdown
 With `tests.kind: repo-gherkin`, the tests adapter finds a story's scenarios under `scenarios_dir` and runs them with `run_tags`, so a repo that holds scenarios needs both.
```

- [ ] **Step 6: Check and commit**

```bash
scripts/check-references.py && scripts/check-skills.sh && claude plugin validate --strict .
git add skills/roost-config/SKILL.md skills/roost-config/references/config-schema.md
git commit -m "feat(#138): roost-config supports tests.kind repo-gherkin"
```

### Task 1.4: Wording that assumes a test is a ticket

**Goal:** `run-slice`, `slice-handoff` and `release-qa` say what they need in the operations' terms, and read the same for Xray and eval teams.

**Files:**
- Modify: `skills/run-slice/SKILL.md:74`, `:206`
- Modify: `skills/slice-handoff/SKILL.md:36`, `:83`
- Modify: `skills/release-qa/SKILL.md:72`, `:75`

**Acceptance Criteria:**
- [ ] No changed line names labels, statuses or links for tests, except as what "Mark a test automated" does.
- [ ] For Xray, each line still means the same (labels and statuses are what "Mark a test automated" sets there).

**Verify:** `grep -nE "tests' labels|labels and statuses|unlabelled|are linked to NEXT|linked to the story, unmarked" skills/run-slice/SKILL.md skills/slice-handoff/SKILL.md skills/release-qa/SKILL.md` → no output

**Steps:**

- [ ] **Step 1: `run-slice/SKILL.md:74`**

```markdown
3. **The tracker:** STORY's status, its tests ("A story's tests") and whether each is marked automated ("Mark a test automated"), and any tickets already created from this slice (linked "relates to"), so they aren't filed twice.
```

- [ ] **Step 2: `run-slice/SKILL.md:206`**

```markdown
- A test created for an exploratory bug the user deferred may stay unmarked ("Mark a test automated"): it's automated with that bug's fix, not in this slice. List it in the slice-done comment's **Left open** table with the bug and where the bug went.
```

- [ ] **Step 3: `slice-handoff/SKILL.md:36`**

```markdown
- **Every test in the epic:** each story's tests in EPIC so far ("A story's tests"), and whether each is marked automated ("Mark a test automated"), leaving out retired tests (the tests adapter's "Retire a test").
```

- [ ] **Step 4: `slice-handoff/SKILL.md:83`**

```markdown
- Check NEXT's tests exist ("A story's tests" for NEXT) and match what NEXT's kickoffs say to automate.
```

- [ ] **Step 5: `release-qa/SKILL.md:72`, `:75`**

```markdown
- **The covering test is already marked automated:** don't add to it, which would make that false. Create a new test for the bug's scenario ("Create a test"), for the story, not marked automated until it's automated.
```

```markdown
Say in the bug which test it is, and link the two ("relates to") when the test is a ticket. Whoever fixes the bug automates that test as part of the fix.
```

- [ ] **Step 6: Check and commit**

```bash
scripts/check-references.py && scripts/check-skills.sh
git add skills/run-slice/SKILL.md skills/slice-handoff/SKILL.md skills/release-qa/SKILL.md
git commit -m "fix(#138): tests are named by the adapter's operations, not as tickets"
```

### Task 1.5: `verify-slice-tests`' split defers to "Split a test"

**Goal:** Steps 7 and 8 name no result of their own, so decision 5 and Xray's new test both fit.

**Files:**
- Modify: `skills/verify-slice-tests/SKILL.md:36`, `:38`

**Acceptance Criteria:**
- [ ] Step 7 shows the existing test's scenarios and where the rest go, as "Split a test" says.
- [ ] Step 8 marks only the existing test automated.
- [ ] `xray-split-makes-new-test` and `repo-gherkin-split-leaves-suite` both pass.

**Verify:** the two cases, 3 of 3 each

**Steps:**

- [ ] **Step 1: `:36`**

```markdown
   - **The proposed split** ("Split a test"): the existing test keeps every automated scenario (a scenario that's only partly automated becomes the part the automation checks), and the part that isn't automated goes where "Split a test" says. Show both in full.
```

- [ ] **Step 2: `:38`**

```markdown
8. **If the user approves a split,** carry it out as "Split a test" says, saving the existing test's scenarios to a local file first and saying where ("Update a test's scenarios"). Re-run the existing test, push any change, and mark it automated. Nothing that took the part that isn't automated is marked automated.
```

- [ ] **Step 3: Run the two split cases, then commit**

```bash
for c in repo-gherkin-split-leaves-suite xray-split-makes-new-test; do
  claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --case "$c"
done
git add skills/verify-slice-tests/SKILL.md
git commit -m "fix(#138): verify-slice-tests' split follows the adapter's Split a test"
```

Expected: both 3 of 3.

### Task 1.6: All of #138's cases pass

**Goal:** Every #138 case passes 3 of 3, and the existing test-handling cases still pass.

**Verify:**

```bash
for c in verify-repo-gherkin-scenarios repo-gherkin-needs-e2e repo-gherkin-split-leaves-suite xray-split-makes-new-test verify-not-automate manual-test-not-automated verify-with-eval-cases xray-refuses-without-scenarios bdd-for-existing-feature; do
  claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --case "$c"
done
```

Expected: every case 3 of 3. A case that fails gets one more try (`tests-evals.md:36`); read the failing grader's verdict and the reply, then fix the adapter or skill text, never the grader. Record the results in an `evals:` comment on #138, with the commit.

### Task 1.7: PR

- [ ] `grep -rn repo-gherkin skills/` → only `skills/roost-config/SKILL.md`, `skills/roost-config/references/config-schema.md` and `skills/roost-config/references/tests-repo-gherkin.md`.
- [ ] All four repo checks pass.
- [ ] Push, `gh stack submit`, title `feat(#138): verify a story's scenarios in the repo`. The description names the skills whose wording changed outside `roost-config` (checklist 7). Add the `run-evals` label (it runs every case, since `roost-config` changed).
- [ ] Add the PR to the epic's Release order comment.

---

## Story #139: Write scenarios before and after the code (branch `issue-139-roost`, stacked on `issue-138-roost`)

Waits for #138's adapter ("Create a test", "Write scenarios", "The `scenarios:` comment").

### Task 2.1: The eval cases, test-first

**Files:**
- Create: `evals/phase-5-drafts-scenarios/prompt.md`, `graders/drafts-on-stories.md`, `graders/no-xray-filing.md`
- Create: `evals/bdd-files-to-repo/prompt.md`, `graders/files-to-repo.md`, `graders/no-xray-filing.md`
- Modify: `CONTRIBUTING.md` (evals table)

**Steps:**

- [ ] **Step 1:** Copy both cases word for word from #139's `evals:` comment.
- [ ] **Step 2:** Add the rows:

```markdown
| `phase-5-drafts-scenarios` | With `repo-gherkin`, `shape-epic` phase 5 drafts each story's tests as a `scenarios:` comment with full `.feature` text tagged with its key, puts a cross-cutting test on the last story it needs, and files no Xray tests |
| `bdd-files-to-repo` | With `repo-gherkin`, `live-verified-bdd` files approved scenarios as a `.feature` file on the current branch, tagged with the story's key, not through `create-xray-test` |
```

- [ ] **Step 3:** Run both on `issue-138-roost`'s head. Record each result: either may already pass, because #138's adapter covers both cases (Contradictions, C6). That's recorded, not forced to fail.
- [ ] **Step 4:** Commit: `test(#139): eval cases for writing scenarios before and after the code`.

### Task 2.2: `shape-epic` phase 5 and 6 wording

**Files:**
- Modify: `skills/shape-epic/references/phase-5-tests.md:41`, `:50`
- Modify: `skills/shape-epic/references/phase-6-guide.md:26`, `:41`

**Steps:**

- [ ] **Step 1: `phase-5-tests.md:41`**

```markdown
   - The slice-to-test mapping, so each test goes with its story (a cross-cutting test with the last story it depends on), and gets what "Create a test" copies from that story (its Components, for a test that's a ticket)
```

- [ ] **Step 2: `phase-5-tests.md:50`**

```markdown
The epic's tests, each with its story ("A story's tests"), with the manual ones marked and described.
```

- [ ] **Step 3: `phase-6-guide.md:26`**

```markdown
   - Test pills: which tests should pass after this slice, each named as the tests adapter names a test (a key, a case's name, a `.feature` file)
```

- [ ] **Step 4: `phase-6-guide.md:41`**

```markdown
- Make test pills clickable (link to where the test lives: its ticket, its file, or the story's comment that drafts it)
```

- [ ] **Step 5:** `scripts/check-references.py && scripts/check-skills.sh`; commit `fix(#139): shape-epic names tests the adapter's way`.

### Task 2.3: `live-verified-bdd` hands off with its repo and branch

**Files:**
- Modify: `skills/live-verified-bdd/SKILL.md:91-94`

**Steps:**

- [ ] **Step 1:** Add a bullet to the hand-off list, after "each test's title and its scenarios":

```markdown
- the repo and branch this session is on, since "Create a test" may write the file there
```

- [ ] **Step 2:** Commit `feat(#139): live-verified-bdd files scenarios where the adapter says`.

### Task 2.4: All of #139's cases pass, and the PR

- [ ] Run `phase-5-drafts-scenarios`, `bdd-files-to-repo`, `shape-epic-starts-with-problem`, `design-without-ui-is-architecture`, `prototype-stops-without-design-system`, `bdd-for-existing-feature`: each 3 of 3. Fix the skill or adapter text on a failure, never a grader. Record in an `evals:` comment on #139.
- [ ] `grep -rn repo-gherkin skills/` → unchanged from #138.
- [ ] Push, `gh stack submit`, title `feat(#139): write scenarios before and after the code`, `run-evals` label; Release order comment.

---

## Story #140: Manual scenarios (branch `issue-140-roost`, stacked on `issue-139-roost`)

Waits for #138's adapter.

### Task 3.1: The eval cases, test-first

- [ ] Copy `manual-scenario-not-automated` and `no-manual-without-label` word for word from #140's `evals:` comment. Leave `manual-test-not-automated` (the Xray case) unchanged (Contradictions, C1).
- [ ] Rows:

```markdown
| `manual-scenario-not-automated` | With `repo-gherkin`, `verify-slice-tests` reports a scenario tagged manual by its `manual run:` comments, never as not automated, and flags a file that mixes manual and automated scenarios |
| `no-manual-without-label` | With `repo-gherkin` and no `tests.manual_label`, `shape-epic` phase 5 writes no manual scenarios; a one-off check goes into the story's acceptance criteria |
```

- [ ] Run both on `issue-139-roost`'s head. Expected: `manual-scenario-not-automated` fails (no manual tests yet); `no-manual-without-label` may pass (Contradictions, C6). Record both.
- [ ] Commit `test(#140): eval cases for manual scenarios`.

### Task 3.2: The adapter's "Manual tests"

**Files:**
- Modify: `skills/roost-config/references/tests-repo-gherkin.md` (the "Manual tests" row, "Running a story's scenarios", and a new section)
- Modify: `skills/roost-config/references/config-schema.md:44`

**Steps:**

- [ ] **Step 1:** The table's row:

```markdown
| **Manual tests** | "Manual tests", when the config has `tests.manual_label`. Without it there are none: a check no scenario can make goes into the story's acceptance criteria. |
```

- [ ] **Step 2:** In "Running a story's scenarios", after the first sentence:

```markdown
When the config has `tests.manual_label`, always leave the manual scenarios out: `{tags}` is `@PROJ-1250 and not @manual`, whatever the team's own command does.
```

- [ ] **Step 3:** Add the section, after "Retiring a test":

````markdown
## Manual tests

Some checks are one-off on purpose: run once, by hand, against a real environment, because automating them would cost more than it proves. When the config has `tests.manual_label`, such a check is a manual scenario:

- **Tagged** `@<tests.manual_label>`, decided while shaping (`shape-epic` phase 5), never later to get out of automating something.
- **Its Gherkin description says how to run it:** the free text under `Scenario:` gives the environment, the steps or commands, and what passing looks like, and a line `When: after release` if it can only pass after the epic ships. Its steps are for reading; they have no definitions.
- **A file is all manual or all automated.** A file that mixes them is reported as needing its manual scenarios moved into their own file; nothing is deleted.
- **Closed by a recorded run, not by automation.** Whoever runs it adds a comment on the story starting `manual run:` with the date, who ran it, the environment, a pass or fail for each scenario, and the evidence. Its status comes from the newest `manual run:` comment; there's nothing else to close.
- **Who runs it:** the session of the repo that owns the story's work runs what it can read-only. Anything that changes a shared or production resource, needs access the session doesn't have, or is in `deploy.runbooks.never_run_against`, goes to the user as a 🙋 **Your turn** action; the session records the run from their answer.
- **Not automated, ever:** no skill reports a manual scenario as "not automated", proposes splitting it, or writes step definitions for it. It's run once.
- **After release:** one with `When: after release` isn't part of any slice; it's listed with the user as its owner, and the release call doesn't wait for it.
- **The team's own run commands leave the tag out** (`not @manual`), so CI never runs them.
````

- [ ] **Step 4: `config-schema.md:44`**

```markdown
| `manual_label` | *Optional, for `xray` and `repo-gherkin`.* The label (with `repo-gherkin`, the tag) for a test that's run by hand on purpose, once, against a real environment, and closes on a recorded run instead of automation (see "Manual tests" in the tests adapter). Leave it out to allow no manual tests. |
```

- [ ] **Step 5:** `scripts/check-references.py && claude plugin validate --strict .`; commit `feat(#140): manual scenarios in the repo`.

### Task 3.3: All of #140's cases pass, and the PR

- [ ] Run `manual-scenario-not-automated`, `no-manual-without-label`, `manual-test-not-automated`, `verify-repo-gherkin-scenarios`: each 3 of 3. If `manual-by-record` fails only on `dns.feature`, apply Open question 5's fallback: add to `verify-slice-tests` step 2 "A test that mixes manual and automated scenarios: flag it and propose separating them", run again, and commit `fix(#140): verify-slice-tests flags a test that mixes manual and automated`.
- [ ] Record in an `evals:` comment on #140. Push, `gh stack submit`, title `feat(#140): manual scenarios`, `run-evals` label (every case); Release order comment.

---

## Story #141: Offer it in setup (branch `issue-141-roost`, stacked on `issue-140-roost`)

Waits for #138 to #140: `setup` offers the kind only once everything works.

### Task 4.1: The eval case, test-first

- [ ] Copy `setup-offers-repo-gherkin` word for word from #141's `evals:` comment. Row:

```markdown
| `setup-offers-repo-gherkin` | For a team with `.feature` files and no test-management tool, `setup` offers Gherkin files in the repo, suggests each repo's `e2e` keys from its Cucumber config, proposes a manual tag the run commands leave out, and writes no Xray keys |
```

- [ ] Run it: expect FAIL (setup offers only Xray or eval cases). Commit `test(#141): eval case for setup offering repo-gherkin`.

### Task 4.2: `setup`

**Files:**
- Modify: `skills/setup/SKILL.md:27`, `:34`, step 4's list (`:51-62`)

**Steps:**

- [ ] **Step 1: `:27`,** name the third example: after "`examples/config.github-only.yml` for one that uses only GitHub (…)", add ", or `examples/config.repo-gherkin.yml` for one whose Cucumber scenarios are `.feature` files in its own repo".
- [ ] **Step 2: `:34`**

```markdown
2. **Tests:** Xray, eval cases in the repo (a Claude Code plugin's `evals/`, run with `claude plugin eval`), or Gherkin files in the repo (Cucumber `.feature` files with no test-management tool). For Xray, whether `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set; for evals, the folder and the command that runs one case; for Gherkin files, each repo's `e2e`, suggested from its Cucumber config (`cucumber.js`, `cucumber.yml`, the test script in `package.json`) for the user to confirm: `scenarios_dir`, `run_tags` with `{tags}`, and `tag_style` (the story's key as a tag). Ask whether some checks are run by hand on purpose: if so, suggest `tests.manual_label` (for example `manual`), and say the run commands must leave that tag out (`not @manual`).
```

- [ ] **Step 3:** Step 4's list, after "for eval cases: …":

```markdown
- **for Gherkin files:** each repo with `e2e.scenarios_dir` has that folder, and its `e2e.run_tags` holds `{tags}`;
```

- [ ] **Step 4:** `scripts/check-references.py`; commit `feat(#141): setup offers Gherkin files in the repo`.

### Task 4.3: README and the example config

**Files:**
- Modify: `README.md:67`
- Create: `examples/config.repo-gherkin.yml`

**Steps:**

- [ ] **Step 1: `README.md:67`**

```markdown
| Test management | `tests.kind` | Xray (Cucumber scenarios), eval cases in the repo, [Gherkin files in the repo](skills/roost-config/references/tests-repo-gherkin.md) | |
```

- [ ] **Step 2: `examples/config.repo-gherkin.yml`:** copy `examples/config.github-only.yml`, then set `tests` and the repo's `e2e`, and change its header comment to say it's for a team on GitHub Issues whose Cucumber scenarios live in its web repo:

```yaml
tests:
  kind: repo-gherkin
  manual_label: manual

repos:
  - name: acme-web
    github: acme/acme-web
    role: frontend
    session: Web session
    order: 1
    kickoff_title: Kickoff (acme-web)
    branch_suffix: web
    owns: the web app and its Cucumber e2e suite
    tests: component tests next to the components, and Cucumber scenarios in features/
    local_stack: false
    e2e:
      run_all: npm run test:bdd -- --tags "not @manual"
      run_tags: 'npm run test:bdd -- --tags "{tags}"'
      scenarios_dir: features/<area>/
      tag_style: "the story's key as a tag (@issue-87)"
```

- [ ] **Step 3:** `scripts/check-references.py && scripts/check-private-details.test.sh && scripts/eval-cases.test.sh`; commit `docs(#141): README and an example config for repo-gherkin`.

### Task 4.4: The example config loads, all cases pass, and the PR

- [ ] **The example loads in `roost-config`:**

```bash
ROOST_CONFIG="$PWD/examples/config.repo-gherkin.yml" claude -p --plugin-dir . "Use roost-config: which config is roost using, and is every key in it supported?"
```

Expected: it names `examples/config.repo-gherkin.yml`, team `Acme`, and reports no unsupported kind and no missing `e2e` keys. Paste the output in the PR.

- [ ] Run `setup-offers-repo-gherkin` and `setup-asks-production-and-voice`: each 3 of 3. Record in an `evals:` comment on #141.
- [ ] `grep -rn repo-gherkin skills/` → only the adapter, `roost-config`, `config-schema.md` and `setup`.
- [ ] Push, `gh stack submit`, title `feat(#141): offer Gherkin files in the repo in setup`, `run-evals` label; Release order comment.

---

## Self-review

- **Spec coverage:** each design decision has a task: 1 (Tasks 1.2, 2.2, 2.3), 2 and 3 (Task 1.2), 4 (Task 3.2), 5 (Tasks 1.2, 1.5), 6 (Task 1.2). Each "Changes elsewhere" item: `roost-config` (1.3), schema (1.3, 3.2), `setup` (4.2), README (4.3), examples (4.3), wording (1.4, 1.5, 2.2), eval cases (1.1, 2.1, 3.1, 4.1). Each story's acceptance criteria map to a case or a PR check ("How each scenario is checked").
- **Placeholders:** none; every changed line's new text is given. The adapter text depends on Open questions 1, 2 and 6; Task 1.2 says to change it only where Alan's answer differs.
- **Names:** the operation names match `tests-evals.md:13-25` exactly; the comment is `scenarios:` throughout; branch names are `issue-13x-roost` (`tracker-github.md:8`, `branch_suffix: roost`).
