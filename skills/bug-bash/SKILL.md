---
name: bug-bash
description: Fix a list of bugs from the tracker in this repo, one branch each, test-first, with each fix placed by its parent (on the epic's GitHub stack for a bug in an unreleased epic, or its own PR from main for a standalone bug), moving each ticket through In Progress and Ready for Release. When a fix needs another repo, hand it off with pasteable comments instead of touching it. Use when the user gives a list of bugs to fix, says "bug bash", or pastes a "Big Bug Fix Bash" prompt.
---

# Bug Bash

Fix several bugs in one session, each on its own branch, and keep the tracker in step. Each fix goes where its bug belongs: on its epic's stack, or on its own PR from `main` (see "Where the branch goes").

**First, load the team config with `roost-config`.**

## Inputs

Ask for anything missing, in one message:

- **The bugs:** ticket keys.
- **This repo:** which of the config's `repos` this session is in (its working directory usually says). Every other repo is off-limits.
- **Where each fix goes** comes from the bug itself (see "Where the branch goes" below). Ask only if the user named a stack that contradicts it.
- Anything the user wants different from the defaults below.

## Where the branch goes

Read the bug's parent in the tracker:

| Bug | Branch | PR | Release |
|---|---|---|---|
| **Part of an epic that isn't released yet** (see below) | On top of the epic's stack in this repo: the highest branch of that epic, found with `gh stack` or the epic's **Release order** comment | On the epic's stack, with the "Stacked on" banner; add it to the epic's Release order comment | Ships with the epic |
| **Standalone** (no parent, or its epic is already released) | From `main` | Its own PR, not on any stack | Released on its own once merged |

**Released** means the epic's code is in production, not that the epic ticket is closed: an epic can stay open after release for its person-owned tasks. It's released when its **Close-out** comment says what's in production (`close-out-epic` step 6), or its stories carry a fix version that's released. If neither says so, treat it as unreleased.

Name the branch for the ticket (`PROJ-XXXX`). Several bugs of the same epic stack on each other in the order given.

## For each bug, in order

1. **Read the ticket** and its links. Reproduce or confirm the problem in code before fixing it. If the ticket is wrong or already fixed, say so, move nothing, and go to the next bug.
2. **Assign it and start it:** assign the ticket to the person running this session (see "Who am I" in the tracker adapter) and move it to `tracker.statuses.in_progress`.
3. **Branch** where the table above says. For an epic bug, follow the `stacked-prs` skill.
4. **Test first.** Write a test that fails because of the bug, watch it fail, then fix. If a test-first approach isn't reasonable, make sure at least one test covers the problem afterwards. If the bug has a test linked in the tracker (`release-qa` files one with every behaviour bug), automate its scenario as part of the fix with `automate-xray-tests`, and label and close that test once it passes. If it has none and the behaviour could regress, add one first with `create-xray-test` (a new test when the covering one is already labelled `tests.automated_label` and done).
5. **Run** the relevant unit, functional and e2e tests. You may start and stop the local stack as needed (`stack.how`).
6. **Commit** (signed, if `vcs.signed_commits`), push, and open the PR: on the epic's stack with the "Stacked on" banner (`stacked-prs`), or, for a standalone bug, against `main`. The PR title follows `vcs.pr_title`, for example `fix(PROJ-XXXX): …`.
7. **Move it to `tracker.statuses.ready_for_release`** once it meets the definition of done below.

## When a fix needs another repo

Don't change the other repo. Instead, for that ticket:

1. Add a comment describing the work **this repo** needs, and one for each **other repo** that needs work. Each must be pasteable into a fresh AI session and work on its own. Follow the `cross-repo-handoff` skill for their shape.
2. Don't make the code change here either, and don't push that branch.
3. Move the ticket back to `tracker.statuses.todo`.

## Definition of done, per bug

- The branch is pushed and its PR is where the table above says.
- All tests pass locally and on GitHub.
- Every PR below it in the stack is ready.

## Rules

- **Signed commits,** when `vcs.signed_commits` is true. If signing is blocked (`vcs.signing_blocker`), stop and say so in one line; don't keep retrying. The user may be away, so ask them up front to keep it unblocked.
- **No worktrees.** Stage your own files by path.
- **Use the local stack freely.** Start or stop it whenever a fix or test needs it, as `stack.how` says, and never use `stack.never`. If the config has `stack.telemetry.logs`, check the stack's own errors with it before calling a fix done.
- **A fix that adds a migration**, when `deploy.migrations_run_on_deploy` is false, needs a deploy note: the "Migrations to apply" comment and pre-deploy sub-tasks described in `stacked-prs`. Add or update them yourself, and say so in the report.
- **Tickets you create** (for problems found along the way) get the epic as parent, Components, and a "relates to" link to the bug they came from.
- **Stay on the list.** Note unrelated problems you find in the final report, don't fix them.

## Report

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then start with the outcome: "All 7 bugs handled: 5 Ready for Release, 2 back in To Do with hand-offs." Then one table:

| Bug | Branch / PR | Status | Note |
|---|---|---|---|
| PROJ-XXXX | `PROJ-XXXX-…` / #NNN | Ready for Release | |
