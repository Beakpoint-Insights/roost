---
name: run-bug
description: Fix one or more bugs (or follow-up tasks) from the tracker by driving the user's repo sessions over cross-session messages, the way run-slice drives a story. Triages each bug first, assigns it to the user and starts it, sends it to the session that owns the code, and tells that session where the fix goes, on the epic's stack when the bug belongs to an unreleased epic or from main as its own PR when it's standalone. For a fix that needs more than one repo it builds each repo's part in order, restarting the stack between them. Then verifies the fix with a test that failed first, the ticket's test scenario if it has one, and CI green. Starts without asking and stops only for the user's decisions and real blockers. Never edits any repo itself. Use when the user says "fix PROJ-X", "run bug PROJ-X", "have the API agent fix this", or "tackle these bugs". Run it from a separate orchestrator session, not from inside any of the repos.
---

# Run Bug

You coordinate a bug fix the way `run-slice` coordinates a story. You never edit, build or run tests in any repo yourself. One session per repo in the config's `repos` does the work, through `SendMessage`. Find them, talk to them and wait for them exactly as `run-slice` describes ("Find the sessions" and "How to talk to the sessions").

**First, load the team config with `roost-config`.**

Being asked to fix the bug is the go-ahead. Don't ask for another one. Tell the user what you started, and stop only for their decisions and real blockers. While a session works, give the user `run-slice`'s 5-minute progress updates, without being asked: its three formats and its update prompt, with `{STORY}` the bug being worked on and `{LOG}` the first bug's key (`<team.state_dir>/<first bug>-updates.md`).

## Inputs

- **BUGS:** one or more ticket keys. A follow-up Task is handled the same way as a Bug.
- The session for each repo the fixes touch must be open. If one isn't, that's a blocker: ask the user to open it, and stop.

## 1. Triage

For each ticket, judge it the `triage-ticket` way, by reading the ticket and the code, without changing anything:

- **Real, and the ticket is right:** go on.
- **Wrong, already fixed, or not worth fixing:** don't start it. Put it in one message to the user with what you found and a recommendation (close it, change it, or fix something else), and wait for their decision on those tickets only. Carry on with the others.

## 2. Decide where each fix goes

Read each ticket's parent:

| Bug | Where the fix goes | What it waits for |
|---|---|---|
| **Part of an epic that isn't released yet** | On top of the epic's stack in the repo that owns the code, as its own branch named for the ticket | Ships with the epic. Add its PR to the epic's **Release order** comment, and keep the epic's **Carry-over** comment current. |
| **Standalone** (no parent, or its epic is already released) | A branch from `main` and its own PR | Released on its own once merged |

**Released** means the epic's code is in production, not that the epic ticket is closed: an epic can stay open after release for its person-owned tasks. It's released when its **Close-out** comment says what's in production (`close-out-epic` step 6), or its stories carry a fix version that's released. If neither says so, treat it as unreleased.

Several bugs of one epic stack on each other in the order the user gave.

**Which repo:** the one whose code is wrong, from the ticket's Components, each repo's `owns`, and the code. A bug that needs more than one repo follows step 4.

## 3. Start each bug

1. Assign it to the person running this session (see "Who am I" in the tracker adapter) and move it to `tracker.statuses.in_progress`.
2. Send it to the owning session: "Use the `bug-bash` skill for PROJ-X." Then give the branch and base from step 2, for example: "Branch `PROJ-X` stacked on `PROJ-2790-backend`" or "Branch `PROJ-X` from `main`, its own PR". Add:
   - a PR title that follows `vcs.pr_title`, for example `fix(PROJ-X): …`;
   - a test that fails first, then the fix;
   - if the bug has a test, automate its scenario (`automate-xray-tests`); if it has none and the behaviour could regress, add or update one first (the tests adapter's "Create a test" or "Update a test's scenarios");
   - for a repo others depend on: after the fix, `stack.restart_after_api_change` and check the fix on the running stack;
   - judge CI by each check's newest completed result, and don't re-run cancelled runs;
   - send the report as the last thing it does, with no promise of a later report.
3. End the message with the report request: **Status**, **Branch and PR**, **Commit**, **Tests run** (pass/fail counts), **Live check** (what was checked on the running stack), **CI**, **Concerns** (everything noticed), and **Needs from the user**. Every claim about the code or data cites its `file:line`, or the query and its result; anything not checked says "unknown", never a guess.

Send one session several bugs in one message only when they're in the same repo and the same epic; otherwise one message per bug.

## 4. A bug that needs more than one repo

1. Write each repo's part with `cross-repo-handoff`.
2. Send them in `repos` order, each to its session, on its branch from step 2. Wait for each report before the next.
3. Before sending a part to a repo with `depends_on`, ask `stack.owner_repo`'s session to `stack.restart_after_api_change` on the new build, and check yourself that the stack serves the change.
4. A dependent repo's part follows its `contract` (for example regenerating a client against the running API, never checking out the other repo).

## 5. Verify and close

A bug is done when all of these are true:

- the fix's test failed before the fix and passes after;
- its test scenario, if any, is automated and passing, and the test is marked automated (the tests adapter's "Mark a test automated");
- its PR is where step 2 says, and every check's newest completed result passes;
- for an epic bug, its PR is in the epic's Release order comment;
- if it added a database migration and `deploy.migrations_run_on_deploy` is false, a deploy note covers it: the **Migrations to apply** comment and the staging and production pre-deploy sub-tasks, on the epic's deploy ticket or, for a standalone bug, on the bug itself (see `stacked-prs`). Add or update them if they're missing.
- the owning session ran `/code-review` on the fix's own diff (its branch against the branch below it, or `main` for a standalone bug), and each finding is fixed, or decided by the user like any other finding.

Then move the ticket to `tracker.statuses.ready_for_release` (a session that already did is fine; read it back). New problems a session found along the way become tickets for later only with the user's decision: list them in the report with a recommendation.

## Report to the user

Anything the user must do first, in a 🙋 **Your turn** block (leave it out when there's nothing). Then one line: "PROJ-2822 fixed on the PROJ-2306 stack (#580), Ready for Release." Then one row per bug:

| Bug | Where | PR | Test | Status |
|---|---|---|---|---|
| PROJ-2822 | PROJ-2306 stack | #580 | `ProcessRequest_SpanWithoutAttributes_…` failed first, passes | Ready for Release |
