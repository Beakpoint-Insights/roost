---
name: slice-handoff
description: Close out a finished slice of an epic before the next one starts. Sorts everything the slice left open (follow-up tickets, deferred bugs, unautomated scenarios) into the next slice, before release, or later; keeps one Carry-over comment on the epic; runs every test in the epic so far, so a later slice can't quietly break an earlier one, and makes the tracker match; rewrites the next slice's kickoff comments so they're current; and checks every repo's stack is healthy. Use after run-slice finishes a slice (its last step runs this), or when the user says "wrap up PROJ-X", "get ready for the next slice", "what's carried over from slice 3", or "is the epic still green".
---

# Slice Handoff

A slice rarely ends with nothing left over. Exploratory testing finds bugs that wait, code review produces "ticket for later" items, a later slice reopens an earlier slice's test, and the plan changes under the next slice's kickoff. This skill deals with all of it once, in one place, before the next slice starts.

It changes the tracker and reads GitHub. It changes no code. The one step that runs tests goes to the session in the repo that owns them.

**First, load the team config with `roost-config`.**

## Inputs

- **DONE:** the story that just finished.
- **NEXT:** the next story in the epic's story order. If DONE was the last slice, there is no NEXT: skip step 5, and anything sorted "next slice" becomes "before release".
- **EPIC:** DONE's parent.

## 1. Gather what's open

Read everything first; decide nothing yet. Don't trust that the slice recorded everything: look wider than its links, and compare the sources.

- **The slice's own record:** DONE's "slice done" comment, with its **Left open** table, and its `run-slice checkpoint:` comments. Every checkpoint row should have an outcome you can check: a commit or PR for "fix now", a ticket key for "ticket for later", a reason for "skip". Every ticket in the Left open table should exist, be open, and have EPIC as its parent.
- **Open tickets, found two ways** (the tracker adapter's common searches):
  - linked: open tickets linked to DONE;
  - wide: everything in the project created while the slice ran (from DONE's first kickoff message to its "slice done" comment) whose parent is EPIC or whose text mentions DONE.

  Include anything the epic's **Carry-over** comment already lists as "next slice" for DONE that wasn't done.
- **Compare them.** Each difference is a possible record gap:
  - **A ticket only the wide search finds** is a candidate, not a fact: it shares the epic and the dates, but may belong to other work. Don't change it yet. It goes in step 2's table with "From this slice?" for the user to confirm, and is linked to DONE only if they do.
  - **A checkpoint row with no outcome, or a "ticket for later" with no ticket:** put it in step 2's table; don't create the ticket until the user has seen it.
  - **A ticket already linked to DONE but missing its parent or Components:** set them now; it's DONE's ticket either way (see "Set or clear a parent" in the tracker adapter).

  A concern that only ever lived in a session's report can't be found from the tracker. Step 2 asks the user about anything run-slice's state file mentions that has no tracker record.
- **Every test in the epic:** the tests linked to each story in EPIC so far, with their labels and statuses, leaving out retired tests (resolution `Won't Do`).
- **The stacks:** every PR for EPIC in each repo, its head, its base, and each check's newest completed result (`gh pr view <n> -R <repo.github> --json statusCheckRollup`; ignore runs a newer push cancelled).
- **Plan changes:** commits on the plan branch since the slice started, and the decisions recorded in `<team.state_dir>/DONE.md` if it exists.
- **NEXT's kickoff comments,** one per repo, titled with each repo's `kickoff_title`.

Leave Xray Preconditions out of the open tickets (they're part of the epic's tests), and close any whose tests are all done. Leave manual tests with `When: after release` out too (see "Manual tests" in the Xray adapter notes): they wait for the release, like person-owned tasks; name them in the report. Leave person-owned tasks (labelled `tracker.person_task_label`) out of all of this: they aren't carried-over work. If one's "When" is "after" DONE, put a reminder for its owner in the report's 🙋 **Your turn** block.

## 2. Sort the carried-over work

Put each open item in exactly one place, judging it the `triage-ticket` way (is it real, who does it hurt, how badly):

| Place | When |
|---|---|
| **Next slice** | NEXT changes the same code or screen, or NEXT can't be right without it. It's cheapest to fix while that code is open again. |
| **Before release** | It must be fixed before the epic ships (security, data loss, a 5xx from a public endpoint, a broken main flow) and NEXT doesn't touch it. |
| **Later** | Everything else. It keeps the epic as its parent but doesn't hold up the release. |

Show the user one table, with a recommendation and a one-line reason for each item:

| # | Item | From | Recommendation | Why |
|---|---|---|---|---|
| 1 | PROJ-2819 Get started names the wrong key | 2789 exploratory | Next slice | 2790 changes the key list Get started reads |
| 2 | PROJ-2830 Billing page spacing | From this slice? (found by the wide search) | Later, if from this slice; otherwise leave it alone | Created during the slice under the epic, but not linked to it |

This is the only stop in the skill. Wait for the user's decisions, then carry them out without asking again. A candidate the user confirms as this slice's gets its "relates to" link to DONE, and its parent and Components if missing; one they don't confirm is left untouched.

## 3. Keep the epic's Carry-over comment

EPIC has one **Carry-over** comment (create it the first time), next to its Release order comment. It lists every carried item still open: item, slice it came from, place, and status. Update that comment in place by its ID (see "Edit a comment in place" in the tracker adapter), and read it back afterwards. Rewrite it as one current table each time; don't append history. A finished item leaves the table.

Link each "next slice" item to NEXT as "relates to".

## 4. Check every test in the epic

A later slice can break an earlier slice's test. Prove each one still passes, against the local stack running the newest branch of every repo's stack:

- If the config has an e2e repo, ask its session to run the e2e scenarios for every automated test in the epic so far (`repos[].e2e.run_tags` with `"@PROJ-A or @PROJ-B or …"`), with tags for the stack's real flag state (`stack.flag_state`). Ask each other repo's session to run the tests in its repo that those tests name (the `repos[].e2e.backend_marker` comments), or, with no e2e repo, the tests in its repo that automate the epic's tests. Each reports pass/fail per scenario.
- Make the tracker match the result:
  - **Done and labelled `tests.automated_label`, but failing:** reopen it (`tracker.statuses.todo`), remove the label, file a Bug under EPIC with Components that relates to the failing test and the story that broke it, and sort the bug in step 2.
  - **Has scenarios without automation** (often added by exploratory testing): no automated label and not done. Say in the Carry-over comment which slice automates them, normally the one that fixes the bug they came from.
  - **Manual** (`tests.manual_label`): not run again; it's a one-off check. Done with a passing `manual run:` comment stays done. One of DONE's that isn't, and isn't `When: after release`, is carried over: sort it in step 2 like any open item, with what its description says to run.
  - **Created by a split the user approved** (`verify-slice-tests` step 8; the checkpoint record names it): leave it as it is, done without the label. It has no automation on purpose.
  - **All scenarios automated and passing:** labelled and done.
- Check NEXT's tests exist, are linked to NEXT, and match what NEXT's kickoffs say to automate.

## 5. Bring NEXT's kickoff comments up to date

The kickoffs were written before DONE ran. Read each one, keep a copy, and rewrite it in place (same edit as step 3) so someone could follow it cold today:

- **Branches:** the real names and bases on the stack now (rebases change what a branch stacks on).
- **Plan and contracts:** any section, contract or default that changed during DONE.
- **Carried-over work:** each "next slice" item from step 2, under "Also in this slice", with its key, what done looks like, and its test.
- **Standing rules**, if missing: a PR title that follows `vcs.pr_title`; each dependent repo's `contract`; e2e tags from the stack's real flag state (`stack.flag_state`); migrations applied to the local database the roost config names ("the `stack.database.local` in your roost config", never a database's name or address, since another machine may build the next slice); `stack.how`; screenshots on the story's ticket. Leave the stack rules out of a kickoff for a repo with `local_stack: false`. A kickoff for a repo with `apply_gate` says to post `apply_gate.plan` in the PR and never to apply without the user's approval ("The apply gate" in `roost-config`).

Rewrite each comment as one whole, current text. Don't add "Update:" notes to the end.

## 6. Check the stacks

- Every repo's stack is rebased on current `main`, and every PR's newest completed checks pass. Retitle any PR whose title doesn't follow `vcs.pr_title`.
- The epic's **Release order** comment lists every PR in deploy order, with its deploy (see `stacked-prs`).
- Every PR on a stack belongs to the same deploy. NEXT's branch, if it's in a later deploy than DONE's, is on a new stack (`stacked-prs`, One deploy per stack). Fix NEXT's kickoff branch line if it says otherwise.
- If `deploy.migrations_run_on_deploy` is false, every migration on the stacks is on the epic's deploy ticket: its **Migrations to apply** comment and the staging and production pre-deploy sub-tasks (`stacked-prs`). Compare the stack's migration files with the list, and add whatever is missing.
- When any repo DONE or NEXT touches uses the local stack (isn't `local_stack: false`): the local stack runs the newest branch of each repo that uses it, its migrations are applied to `stack.database.local`, and every `stack.services` URL answers, so NEXT's kickoff starts clean.
- Every repo with `apply_gate` that DONE touched has DONE's plan applied and recorded, and a fresh plan shows no changes. Drift, or a plan nobody applied, is an open item for step 2.
- DONE is at `tracker.statuses.ready_for_release`.

## Report

Anything the user must do goes first, in a 🙋 **Your turn** block, one line per action; leave it out when there's nothing. Then one line: "PROJ-2789 handed off: 3 items into PROJ-2790, 1 before release, 4 later; all 9 epic tests pass." Then:

| Area | Result |
|---|---|
| Carry-over | links to the Carry-over comment, with counts per place |
| Epic tests | pass/fail per test, and anything reopened |
| NEXT kickoffs | what changed in each |
| Stacks | PRs and checks, rebased or not, local stack state |

If DONE was the last slice, end with: "Last slice done. Next: `release-qa` for EPIC."
