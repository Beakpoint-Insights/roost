# Plan the implementation of #34

You are the tech lead agent for this epic, running in the `roost` repo.

**Your job is to plan, not build.** Produce an implementation plan and a set of kickoff prompts for each story. Do not write production code.

---

## 1. Context

**Epic:** #34, "feat: Gherkin files in the repo as the test tool (tests.kind: repo-gherkin)". Its tracker is GitHub Issues in `Beakpoint-Insights/roost`. A file attached to an issue is a gist linked from one of its comments.

Read these first:
1. The epic description, and the stories under it.
2. The artifacts listed below.
3. The eval cases for each story: those already in `evals/` tagged with its key, and the drafts in its `evals:` comment, which you commit first, test-first.

| Order | Story | Slice | Tested by |
|---|---|---|---|
| 1 | #138 | Verify a story's scenarios in the repo | `verify-repo-gherkin-scenarios`, `repo-gherkin-needs-e2e`, `repo-gherkin-split-leaves-suite` |
| 2 | #139 | Write scenarios before and after the code | `phase-5-drafts-scenarios`, `bdd-files-to-repo` |
| 3 | #140 | Manual scenarios | `manual-scenario-not-automated`, `no-manual-without-label` |
| 4 | #141 | Offer it in setup | `setup-offers-repo-gherkin`; on the PR: the example config loads in `roost-config` |

### Artifacts

| Artifact | Where | What it's for |
|---|---|---|
| **Design: the adapter's decisions, its operations table and the changes elsewhere** | PR #137, `docs/design/issue-34-repo-gherkin.md` on branch `issue-34-design-doc` | The target design. Its mermaid diagram renders on GitHub |

There's no build guide for this epic. Each story's description holds its scope, `Repos:` line, acceptance criteria and what you can observe.

**Decisions already made. Don't reopen them:**
- **Scenarios before the code:** drafted on the story in a `scenarios:` comment, full `.feature` text per file; the session that builds the story commits them first, test-first. `shape-epic` never opens branches in a team's repos (design decision 1).
- **Code that already runs:** `live-verified-bdd`, in the repo that holds the scenarios, writes the file on its current branch; otherwise it drafts on the story.
- **A test** is one `.feature` file's scenarios carrying the story's tag, on the scenario or inherited from `Feature:`. Whole-tag match only: `@issue-42` never picks up `@issue-420` (decision 2).
- **Automated** is decided by a run with the repo's existing `e2e.run_tags`: passed is automated, undefined or pending is not automated, failed is failing. Recorded in the story's `scenarios:` comment (each scenario's result and the commit), edited in place. No label, no status, no new config keys (decision 3).
- **Manual scenarios** only when `tests.manual_label` is set: tagged `@<manual_label>`, run instructions and `When: after release` in the scenario's Gherkin description, a file all manual or all automated, closed by a `manual run:` comment on the story (decision 4).
- **Split:** scenarios that won't be automated are deleted from the file and their checks move into the story's acceptance criteria (or become manual scenarios when those are on). Never parked under `@wip` or `@skip` (decision 5).
- **`Background:` and `Feature:` are allowed;** retiring deletes the scenarios in a PR that says why (decision 6).
- **No skill gets a `repo-gherkin` branch.** Every skill already goes through the tests adapter's operations (since #17). Where a step's wording assumes a test is a ticket, reword it in the operation's terms. Success check: `grep -rn repo-gherkin skills/` finds it only in the adapter, `roost-config`, `config-schema.md` and `setup`.
- **Order:** setup and the README come last (#141), so roost doesn't offer `repo-gherkin` before manual scenarios work.
- **Out of scope:** `tests.kind: none`, Linear, BDD runners other than Cucumber, moving tests between Xray and the repo, generating step definitions (`automate-tests`, unchanged).

**Starting points in code. Verify each one; don't trust this list:**
- **roost:**
  - `skills/roost-config/references/tests-xray.md` and `tests-evals.md`: the two adapters; the new `tests-repo-gherkin.md` follows their shape ("In a prompt", operations table, "What a test is", the sections the table names). The design doc's "The adapter's operations" table is the draft.
  - `skills/roost-config/SKILL.md:59` (supported table) and `:74` (adapter list).
  - `skills/roost-config/references/config-schema.md:42-49` (`tests` keys) and `:73` (`e2e`).
  - `skills/verify-slice-tests/SKILL.md`, steps 1-9, which call the adapter's operations.
  - `skills/slice-handoff/SKILL.md:36` ("with their labels and statuses"), `skills/run-slice/SKILL.md:74` ("its linked tests' labels and statuses") and `:206` ("may stay open and unlabelled"): wording that assumes tests are tickets.
  - `skills/shape-epic/references/phase-5-tests.md:41` ("Components where tests are tickets") and `phase-6-guide.md:26, :41` (test pills linking to tickets).
  - `skills/live-verified-bdd/SKILL.md:18` and `:91` (hands off to "Create a test").
  - `skills/setup/SKILL.md:34` (the tests question); `README.md:67` (support table); `examples/config.example.yml:28-33` (tests) and `:60-66` (acme-web's `e2e`).
  - `CONTRIBUTING.md:62-100` (the evals table every new case gets a row in) and `:120` (how `scripts/eval-cases.sh` picks cases by tag).
- **Known gaps to confirm:**
  - `verify-slice-tests` steps 7 and 8 say a split makes "a new test" for the part that isn't automated. Does the adapter's "Split a test" override that wording cleanly for decision 5, or does the step need rewording (in operation terms, not a branch)?
  - Is there any skill other than those above whose wording assumes a test is a ticket with a label or status?
  - `roost-config` has no check today for keys a tests kind needs. Where does the "a repo needs `e2e.scenarios_dir` and `e2e.run_tags`" stop go so it reads like the rest of section 2?
  - The eval prompts name `examples/config.example.yml` "with `tests.kind: repo-gherkin`". Does `scripts/eval-cases.sh` pick them up from their tags as expected?

---

## 2. Set up the plan's branch

1. From `roost`, create a new stack named after the epic:
   ```
   gh stack init issue-34-repo-gherkin
   ```
2. Commit the plan (section 3) to the base branch of that stack.

---

## 3. Write the plan

Use the **superpowers writing-plans** skill. Invoke it; don't imitate it.

1. Save the plan to `docs/plans/2026-11-17-issue-34-repo-gherkin.md`. If the repo already keeps plans somewhere else, use that location.
2. Follow the skill's format: small, test-first tasks with exact file paths and commands.
3. Organize the plan by story, in the order above. Within each story, split it by repo, each only if the story needs changes there:
   - **roost:** the plugin's skills and their references, the example configs, its eval cases and its scripts
   - **Order:** repos go in the order above. Say what each later repo waits for, such as an endpoint, a response field or a migration.
4. Plan testing at every level, not only the epic's tests:
   - unit tests for new and changed logic
   - roost: eval cases in evals/ (scripts/eval-cases.sh picks the ones a change affects), and claude plugin validate --strict .
5. For each of the epic's test scenarios (each grader, for eval cases), decide how it's checked: which repo's tests automate it (a backend test, the e2e suite, or another repo's scripted check), or, for a test labelled as manual, that it stays a manual check, run once and recorded, with no automation built for it. For example, the grader "sorts-by-run" in `verify-repo-gherkin-scenarios` is checked by that eval case, and "the example config loads in `roost-config`" is an acceptance criterion checked on #141's PR. Put that mapping in the plan.
6. Work through the tech lead checklist below. Each item is a general rule followed by what it means for this epic. Give each item its own section in the plan. Where an item doesn't apply, say so in one line.

### Tech lead checklist

1. **Confirm what exists before planning.** Read the code and record what's already there. Don't plan from the ticket text alone. Every finding cites its file and line, or the query you ran and its result. A claim inferred from a name, a date or a comment (a migration's date as the age of the data, a comment as the author's intent) is unchecked until it's checked.
   *In this epic:* Does every skill that handles tests go through the adapter's operations, or does any still name Xray, labels or statuses directly? Does `verify-slice-tests`' split wording fit decision 5? Where does `roost-config` check required keys? Which skills does each new eval case's tags make `scripts/eval-cases.sh` run? Record each answer, with its file and line, in a "Current state" section.
2. **Write the contracts down.** For every new or changed endpoint, event or schema, give the request, the response and the error shapes, and say which side generates or updates the client.
   *In this epic:* the contract is the adapter's operations table: every operation `tests-xray.md` and `tests-evals.md` answer, answered for `.feature` files, with the same operation names, so the skills that call them don't change. And the config: `tests.kind: repo-gherkin` reads each repo's `e2e` (`scenarios_dir`, `run_tags`, `tag_style`, `backend_marker`) and `tests.manual_label`; no new keys.
3. **Name blockers outside the epic.** List each dependency on another epic, team or service, its current status, and how the plan proceeds: build a stand-in, sequence around it, or mark it blocked.
   *In this epic:* #17 (the evals test adapter, which split the test tool out of the skills) is closed as completed. Design PR #137 is open; plan on its decisions. No other dependency.
4. **Plan the rollout.** Say how each branch merges without breaking production: feature flags, migrations, backfills, and what existing customers or data see. Include a **release order** table: every branch in deploy order across every repo, the **deploy** that ships it (Deploy 1, Deploy 2, …), and what each waits for. Branches of one deploy form one stack; a later deploy's branches form their own stack. A repo's stack usually merges and deploys before the stacks of repos that depend on it. End the section with one line, **Rollout needed: yes** or **no**, and why. It's yes when merging and deploying isn't enough on its own: a migration, a backfill or other data change, a feature flag to turn on, setup in another service, or deploys that must happen in a set order.
   *In this epic:* roost ships through release-please; no flags, no data. Existing `xray` and `evals` teams must see no change in behaviour: every reworded step reads the same for them.
5. **Enforce the rules on the server.** List every security, billing or data-integrity rule and where the backend enforces it. The UI hiding something doesn't count.
   *In this epic:* doesn't apply, because roost has no server. The nearest thing: a skill must never mark a test automated, or close a manual one, without a run or a recorded `manual run:` behind it.
6. **Make failures visible.** Name the failure modes and the log line, metric or alert for each, so an operator can see them.
   *In this epic:* the failures are what the user is told: a config missing `e2e.scenarios_dir` or `e2e.run_tags` stops with both keys named; a scenario that couldn't run is "Couldn't run" with the reason, never guessed; a file mixing manual and automated scenarios is flagged.
7. **Keep branches reviewable, and size them by reach.** Aim for one concern per branch. A goal that sounds small can still reach far, so list every caller of every method whose behavior or signature the branch changes, with its file and line. If the callers span more than one subsystem (an importer, a background job and an API, say), the branch is bigger than its goal: split it into more stacked branches, or say up front which callers it changes and why. If a story's work in one repo is large, split it, and say how.
8. **Record open questions.** Put anything you can't settle from the code or these instructions in an "Open questions" section. Don't guess, and don't silently pick an answer.
9. **Check the plan against itself.** Compare every contract and task with the Global Constraints and the decisions in section 1. List each contradiction (for example a contract that changes a default the constraints say stays the same) and resolve it, or put it in Open questions.
10. **Find the hard parts before building.** For every component the plan changes, answer these in a "Hard parts" table, or write "n/a, because …":
    - **Shared state:** can two callers reach it at the same time? What do they share, and what happens when they overlap?
    - **Partial failure:** if it fails halfway, is cancelled, or runs twice, what's left behind? Is a retry or a re-run safe?
    - **Lifetimes:** what's cached, scoped or disposed, and can anything outlive what it depends on?
    - **Real data:** what values, volumes, duplicates and odd rows does the data it reads hold today?
    - **Cost of seeing it:** does any new metric label, log line or stored row grow with the data?

    Then write a short pre-mortem: "This shipped and caused an incident. What was it?" Each answer that matters becomes a rule in the plan, with the test that proves it, and goes into the kickoff of the branch that owns it.
    *In this epic:* the components are the new adapter, `roost-config`'s supported check, `verify-slice-tests`' split steps, `shape-epic` phase 5, `live-verified-bdd`'s filing step, and `setup`'s tests question. Wording shared with `xray` and `evals` teams is the likeliest place to break something.
11. **Check every assumption about the data.** List each thing the plan assumes about stored data: which values exist, what's unique, ranges, counts, which environment has what. Check each one with a read-only query in the environment that matters (usually production), and record the query and its result. If you can't run it there, write the query for Alan to run, and treat the assumption as an open question until the result is in.
    *In this epic:* the "data" is how teams' Cucumber suites look: tags inherited from `Feature:`, area files mixing stories, and Cucumber reporting undefined and pending steps separately from failures (true for cucumber-js; say so if you can't confirm it for other flavours). No stored data.
---

## 4. Stop for approval

When the plan is committed, stop. Reply to Alan with:
- the plan's path and the stack name (or, unstacked, the plan's branch and PR)
- a summary of the plan: for each story, the tasks in each repo and their order
- the "Current state" findings, the blockers and the open questions
- anything in the code that contradicts the decisions in section 1, quoted with its file and line
- any contradiction inside the plan itself (checklist item 9)
- the "Hard parts" table and the pre-mortem (checklist item 10)
- each data assumption with its query and result, and any query Alan must run (checklist item 11)
- for each branch, the callers it reaches outside its own subsystem (checklist item 7)
- the **Rollout needed** line from checklist item 4

**Do not post any tracker comments until Alan approves the plan.** If they ask for changes, update the plan, commit it, and stop again.

---

## 5. After approval: post kickoff comments on each story

**First, if the plan says Rollout needed: yes,** set up the deploy work so it can't be missed:
- Find the epic's deploy ticket: a Task under #34 whose title starts with `Deploy #34`. Create it only if there's none, titled `Deploy #34 (feat: Gherkin files in the repo as the test tool (tests.kind: repo-gherkin)) to staging and production`. Either way, make sure its Components are set. Never make a second one.
- Use the `write-runbook` skill for the rollout in the plan, on that ticket. It writes the runbook in `docs/runbooks/`, with one sub-task of the deploy ticket for each of its stages. The code doesn't exist yet, so this runbook is a **draft**: say so at its top, get the stages and their sub-tasks right, and write each command as far as the plan allows. The commands are checked against the finished code before release.
- Name the deploy ticket and the runbook in the Release order comment below.

For each of #138, #139, #140, #141, add one tracker comment per repo that has work in the story. Skip a repo with no work.

**roost:** title it `Kickoff (roost)`; its branch suffix is `roost`.

Each comment is a self-contained prompt for a separate coding agent. Write it so the agent needs nothing else. It must include:

1. **Order:** where this repo comes in the story's order. If it depends on another repo that has work in the story, say: "Do not start until the branch `<name>` in `<that repo>` is pushed with the work you need (stacked: merged into the stack). It provides `<endpoint/field>`."
2. **Branch:** "Create a new branch for this work and add it to the stack for its deploy (see `gh stack --help`)." Name that stack: `issue-34-repo-gherkin` for the first deploy, and for a later deploy the stack its first branch started (record each deploy's stack in the Release order comment). Give the branch name, `<story key>-<the repo's branch_suffix>`, and the branch it stacks on. If this branch is in the **same deploy** as the branch below it, say "stacked on `<branch>`". If it's the **first branch of a new deploy**, say "start a new stack for Deploy <N>: base it on `<earlier deploy's top branch>` but don't link it into that stack" (see `stacked-prs`, One deploy per stack). Add: "Give the PR a Conventional Commit title, for example `feat(<story key>): …`; the title check fails on anything else. Don't write cross-repo dependency notes into the PR; add this branch to the epic's Release order comment instead."
3. **Plan section:** the path to the plan, and which section to execute with the superpowers executing-plans skill.
4. **Scope fence. Copy this word for word:**
   > You are the **[repo name]** agent. Change only **[repo name]**. Do not edit any other repo, even for a "quick" fix. If you find you need a change on the other side, stop, write down exactly what you need, and leave it for the other agent.
5. **E2E tests:** which of the epic's tests (by key or case name) and scenarios to automate at this level of the stack, and which belong to the other layer. If none apply at this level, say "none".
6. **Testing:** "The epic's tests in the tracker are the minimum, not the whole job. Write unit tests for every new or changed function, test-first, plus integration tests where code crosses a boundary (database, third-party service, HTTP). Run the full relevant test suite before you open the PR."
7. **Artifacts:** name the exact artifacts and sections the agent should open. Use the tracker attachment names first and the live links second.
   - **Every comment:** the slice card in the build guide, and the sections of the design doc (its decisions and diagrams) that this branch builds.
8. **Contract:** the endpoints and shapes from the plan that this branch produces or consumes. A comment for a repo with a `contract` must include it word for word:
   none (roost has no `contract`).
9. **Only ask for what the agent can do.** Don't require steps a coding agent can't do (for example attaching images to a PR). Screenshots go on the story's tracker issue, linked from the PR.
10. **Rules and tests:** in every comment, include the checklist item 10 rules for the components this branch changes, each with a test that proves it. Comments for repos with server code must also include the checklist item 5 server-side rules, each with a test that proves it.
11. **Failure visibility (repos with server code only):** the logs and metrics from checklist item 6 that this branch adds.
12. **Definition of done:** the story's acceptance criteria, and that all tests pass.
13. **Review each task as it's done. Copy this word for word:**
    > After each task in the plan, before starting the next, review that task's changes: run `/code-review` on its commits, or have a fresh-context reviewer read them. Check each finding against the code, fix the real ones test-first, and say which you dismissed and why, citing file and line. Then ask: **what else in the code does the same job?** Search for code with the same interface, base class, naming or pattern. Change it the same way, or record why it stays different. Don't leave the review to the end of the branch: a fix reviewed only at the end can break the next fix.
14. **Evidence in reports:** "Every claim about the code or data in your reports cites its file and line, or the query you ran and its result. Write "unknown" for anything you didn't check; never a guess."

There's no build guide for this epic: wherever this section says "the slice card in the build guide", use the story's description instead.

Then post one **Release order** comment on the epic: a table of every branch and PR in deploy order across every repo, with a **Deploy** column, and what each waits for. Keep it current as PRs open.

---

## 6. Report back

When the comments are posted, reply with a table with one row per story: a column per repo saying whether its kickoff comment was posted (yes or no), and the order. If the rollout needed a deploy ticket, also give its key, its sub-tasks and the runbook's path.

Don't change anything in the tracker other than the comments, and the deploy ticket and its sub-tasks, described in section 5.
