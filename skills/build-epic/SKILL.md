---
name: build-epic
description: Build an epic from its tech lead prompt to release QA, through the user's repo sessions (one per repo in the team's roost config). If the stories have no kickoff comments yet, it first sends the epic's tech lead prompt to the lead repo's session, brings the plan to the user for approval, and has the kickoffs posted. Then it runs run-slice for each story in order, slice-handoff between stories, the epic's "before release" work, review-epic, close-out-epic and release-qa. Starts without asking and keeps going on its own; stops only for decisions that are the user's (the plan, each slice's checkpoints, each handoff's sorting table) and for real blockers. Answers "where are we on the epic?" from the tracker, GitHub and its state file. Use when the user says "build PROJ-X", "build the epic", "develop PROJ-X", "start building PROJ-X", "do all the slices", "take this epic to release", or the older "run the epic" and "run the rest of PROJ-X". Run it from a separate orchestrator session, not from inside any of the repos.
---

# Build Epic

You coordinate a whole epic the way `run-slice` coordinates one story. You never edit, build or run tests in any repo yourself. One session per repo in the config's `repos` does the work, through `SendMessage`, exactly as `run-slice` describes. The **lead session** is the session of `planning.lead_repo`.

**First, load the team config with `roost-config`.**

Being asked to build the epic is the go-ahead. Don't ask for another one, at the start or between slices. Tell the user what you started and why, and keep going.

## Inputs

- **EPIC:** the epic's ticket key.
- A session for each repo the epic touches must be open. If one isn't, that's a blocker: ask the user to open it, and stop.

## Status: "where are we on the epic?"

Use `run-slice`'s Status for an epic: one row per story in story order, then the step table for the story in progress. Add one line under it: the counts from the epic's **Carry-over** comment ("before release: 2, later: 5"). Read-only; send nothing.

## 1. Find where the epic is

1. **Story order:** the order the epic's build guide or its stories give ("Slice 1", "Slice 2", …); if neither says, the order the stories were created in.
2. **Each story's state:** at `tracker.statuses.ready_for_release` or later is done; otherwise use `run-slice`'s resume check for it.
3. **Your record:** read `<team.state_dir>/EPIC.md` if it exists: the story order, the current story, the session names, and the IDs of the epic's Release order and Carry-over comments. Check it against the tracker and GitHub the way `run-slice` checks its state file.
4. **The epic's comments:** Release order and Carry-over.
5. **Kickoffs and plan:** whether every story has a kickoff comment for each repo it touches (each titled with that repo's `kickoff_title`), and whether a plan already exists: the plan path and stack in your state file, or a plan commit on a `gh stack` named for the epic in the lead repo.
   - **Every story has its kickoffs:** planning is done; go to step 3.
   - **Some stories have kickoffs and others don't:** posting was interrupted. Ask the lead session to post only the missing ones from the approved plan, then do step 2's check (item 5).
   - **No kickoffs, but a plan exists:** planning stopped before or at approval. Pick up at step 2's checkpoint with that plan; don't send the prompt again, which would start a second stack.
   - **No kickoffs and no plan:** start at step 2.

Tell the user in one short table where the epic is and where you're starting, then start.

## 2. Plan the build

Only when the stories have no kickoff comments yet. The plan is written by the lead session, acting as the epic's tech lead, from the prompt `shape-epic` attached to the epic.

1. **Get the prompt:** the epic's attachment `<EPIC> Tech Lead Prompt.md` (see "Read an attachment" in the tracker adapter). If there isn't one, that's a blocker: tell the user to run `shape-epic`'s handoff phase, and stop.
2. **Send it** to the lead session word for word, with the first line "build-epic: plan EPIC as its tech lead". The prompt itself says to stop for approval after the plan, and what to report. As soon as the reply names the plan's path and stack, record them in the state file, so a restart resumes at the checkpoint instead of planning again.
3. **Checkpoint: the plan.** When the lead session replies, show the user its plan in one message: the plan's path and stack, each story's tasks for each repo in order, the current-state findings, the blockers, the open questions, any contradictions it found, and its **Rollout needed** line. Every current-state finding and every contradiction must cite its `file:line`, or a query and its result; send any that doesn't back to the lead session before you show the plan, and never fill the gap from memory. Treat a claim inferred from names or dates (a migration's date as the age of the data, a code comment as the author's intent) as unchecked until it's checked against the data or the user. If the plan says no but it adds a migration, a backfill or a flag, say so and recommend yes. Recommend an answer for each open question. If the user asks for changes, send them to the lead session and show the updated plan; repeat until they approve.
4. **Approve:** tell the lead session the user approved, and to post the kickoff comments and the Release order comment (its prompt's section 5). Wait for its report.
5. **Check:** read every story's comments yourself, not just the report. Every story has its kickoffs, and the epic has a Release order comment. If the rollout is needed, the epic has its deploy ticket with sub-tasks, and the runbook is on the plan's stack. If any are missing, ask the lead session for those only, and check again. Record the plan's path, the stack and the Release order comment's ID in the state file. Then start the first story.

## 3. Build each slice

For each story, in order, from the first that isn't done:

1. Run `run-slice` for it. Its checkpoints stay the user's: the combined review list (step 3) and the exploratory bugs (step 5). Collect each checkpoint's decisions in one message; don't split them into several questions.
2. When the slice is done, `run-slice` runs `slice-handoff` for it. Show the handoff's sorting table; it's the only stop between slices.
3. When the user has answered the sorting table, let `slice-handoff` finish its remaining steps (the Carry-over comment, the epic's tests, the next story's kickoffs, the stacks). Then start the next story straight away, from those updated kickoffs. Don't ask whether to.

Between slices, carry the same sessions on. Say at the top of each kickoff message which story it's for, since the sessions have just worked on another one.

## 4. Before release

Before QA, if `deploy.migrations_run_on_deploy` is false, check the epic's deploy ticket lists every migration on the stacks, with pre-deploy sub-tasks for staging and production (`stacked-prs`). Add whatever is missing.

After the last slice, `slice-handoff` runs with no next slice, so everything it sorts is "before release" or "later".

Manual tests with `When: after release` don't hold up the release call; list them in the final report with the user as their owner.

Person-owned tasks (labelled `tracker.person_task_label`) are never sent to a session. Those whose "When" is before release go in a 🙋 **Your turn** block for their owner, and the release call waits for them; those after release are listed in the final report.

1. Send each "before release" item to the session that owns its code, by kind:
   - **A Bug:** `bug-bash` in that session.
   - **A task or follow-up ticket** (not a Bug): the ticket itself, sent as one instruction (test-first, one commit, pushed on the stack, and the ticket moved to `tracker.statuses.ready_for_release`), with the usual report request.
   - **Unautomated scenarios:** `automate-xray-tests` in the e2e repo's session, for the test they're in. Never for a manual test (`tests.manual_label`).
   - **A manual test not run yet:** to the session of the repo that owns the work it checks, to run and record as `run-slice` step 2 says.
   - **An item that needs more than one repo:** write each repo's part with `cross-repo-handoff`, then send them in `repos` order. Send a dependent repo's part only when the repo it depends on reports done and the stack is restarted. Writing the parts isn't the fix; each has to be built.

   Wait for every report.
2. Refresh the epic's **Carry-over** comment, as `slice-handoff` step 3 does, so fixed items leave the table.
3. Run `slice-handoff`'s step 4 once more, so every test in the epic passes against the newest branches.
4. Run `review-epic` for EPIC: a whole-epic `/code-review` at high effort in every repo (and `/security-review` in the lead repo), with its own checkpoint. Fixes it asks for go back to step 1, and the tickets it files for later are placed in step 5.
5. Run `close-out-epic` for EPIC. Every open ticket gets a place: fixed before release (back to step 1), moved to the epic's follow-up epic, or made standalone, each with a link back and a description that stands on its own. The epic ends with no open tickets except what's being fixed and the deploy ticket.
6. **Refresh the rollout runbook,** if the epic has one. Ask the session of `deploy.runbooks.repo` to run `write-runbook` again on the epic's deploy ticket, against the finished stack: check every command against the code, fill in the literal values, add the migrations and anything else the build changed, and take off the draft mark. The runbook and the deploy ticket's sub-tasks must still match. The new commit goes on top of that repo's stack and into the Release order comment.
7. Ask the e2e repo's session to run `release-qa` for EPIC. It gives the release call. When the config has no e2e repo, there's no browser QA: give the release call yourself, from `slice-handoff` step 4's last run (every automated test passing), every manual test done on a passing run except after-release ones, every `apply:` recorded with no drift, and every "before release" item done.
8. New release-blocking bugs from QA go back to step 1, with the user's decision first. Anything QA finds that can wait goes through `close-out-epic` again. If a fix changes a migration or a rollout command, refresh the runbook again (step 6).

Shipping (merging the stacks in Release order and deploying) isn't part of this skill. A repo with `apply_gate` is different: its plans are applied slice by slice through `run-slice`'s apply checkpoint, so before the release call, check every one of its PRs has its `apply:` comment and a fresh plan shows no changes ("The apply gate" in `roost-config`). Whenever you tell the user a stack is ready to merge, name every PR the merge takes and check each belongs to that deploy (`stacked-prs`, One deploy per stack); if the repos release with a release PR (`deploy.release_tool`, for example Release Please), for the one that follows, run `git fetch origin`, then check `git diff --name-only origin/main origin/<release branch>` shows only the release files. End with the release call, the Release order comment, and the close-out comment saying what was deferred and where it went.

## Keep the state file current

`<team.state_dir>/EPIC.md` holds the roost the run uses (the line from "Which roost is running" in `roost-config`, checked against every session as `run-slice` step 0 does), the story order, the story in progress, the sessions, the Release order and Carry-over comment IDs, and each story's outcome in one line (PRs, tests, what was carried over). Each story's own detail stays in `<team.state_dir>/STORY.md`, which `run-slice` keeps. Update it after every slice and every decision.

## Progress updates

Use `run-slice`'s progress updates: its three formats and its update prompt, word for word, with one log for the epic (`{LOG}` is EPIC, so `<team.state_dir>/EPIC-updates.md`). Each update names the story it's about: `{STORY}` is the story in progress, in the update's heading and its log line.

## Report to the user

Lead with where the epic is ("PROJ-2306: slices 1 to 3 done, slice 4 frontend running"), then a 🙋 **Your turn** block if there's anything to do, then the epic Status table.

At the end: the release call, every PR in Release order with its checks, the tests and their status, the person-owned tasks and manual tests (`When: after release`) still to do after release (with their owners), and what was deferred, taken from the epic's **Close-out** comment (`close-out-epic` clears the Carry-over comment).
