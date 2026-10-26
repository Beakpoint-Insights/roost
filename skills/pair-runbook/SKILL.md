---
name: pair-runbook
description: Run a rollout runbook together with the user, one step at a time. Claude gives the next command and what to expect; the user checks it, runs it and pastes the output; Claude checks the output, fills in the stage's record in the run's working copy, updates the stage's sub-task, and moves on. Claude never runs a command against staging, production, outside services or a shared database itself. Stops at every gate and every failure, resumes from the working copy and the tracker, and after the production rollout updates the epic's build guides to show what shipped. Use when the user says "run the runbook with me", "let's do the PROJ-X rollout", "pair on the deploy", "what's the next runbook step", or pastes command output during a rollout.
---

# Pair Runbook

The user and you run a rollout runbook (written by `write-runbook`) together. You're the navigator: you say what to do, check what happened and keep the record. The user is the driver: they read each command, run it and paste back the output. Nothing changes in any environment except through their hands.

**First, load the team config with `roost-config`.**

## Rules that always apply

- **You never run a rollout command.** Not against anything in `deploy.runbooks.never_run_against` (and always not against staging, production or a shared database), and not "just a read-only check". The user runs every command in the runbook. You may read the runbook and the repo, keep the working copy, and read and update the tracker. The one exception: when the user explicitly hands you a step to do through a connected tool (for example "create the alerts through the monitoring MCP" or "delete the flag with the feature-flag MCP"), do that step, show what you did, and record it as done by you at their request.
- **Before asking the user anything, re-read their recent messages.** The answer is often already there.
- **One command per turn.** Give one command (or one block the runbook groups as a single action), then wait for its output. Never queue up several.
- **Secrets stay out.** Never ask for a secret's value. Before a command whose output includes one (a key, a connection string, a webhook secret), say which part to blank out before pasting. If the user pastes a secret anyway, say so, and don't repeat it in your reply, the record or the tracker.
- **The template stays as it is.** Fill in the working copy, never the runbook in the repo. If a command in the runbook turned out wrong, record what was run instead and add it to the working copy's **Runbook fixes** list, to fix after the run.
- **Plain language.** Say what a stage proves and what the output means, in a sentence each.

## Inputs

- **The rollout ticket** (the deploy ticket, for example PROJ-2795). Its description names the runbook; each stage of the runbook is one of its sub-tasks, with the same number and title.

## Words used here

- A **stage** is one numbered unit of the runbook with its own sub-task (stage 6, "Apply the migrations to staging", is one sub-task). The runbook may call it a step.
- A stage holds one or more **commands** (6a, 6b …), each with its expected output, and one **Record** block.
- A **gate** is a go/no-go decision the runbook puts after a stage or a group of stages (Gate T after stages 5 to 8). A stage whose "Done when" names a gate isn't done until that gate is passed.

## 1. Set up, or resume

1. **Read the runbook.** The ticket says where it is. Read the version on `main` in `deploy.runbooks.repo`; if it isn't merged yet, read the branch the ticket names, and tell the user which one you're using.
2. **Check it matches the tracker.** Every stage has its sub-task with the same number and title, and every open sub-task is a stage. If they don't match, stop and show the difference; the user decides which is right before anything runs.
3. **Find the working copy.** The runbook's "How to record this run" names it (for example `~/PROJ-2795-run-<date>.md`). Look for one from an earlier session.
   - **None:** create it by copying the runbook, then ask the user to start the transcript the runbook asks for (`script -a …`) in the terminal they'll run commands in. Fill in the run header with them: date, operator, the environments this session will touch.
   - **One exists:** resume from what's recorded, not from the first blank. For each stage, read its Record (result **pass**, **fail**, or partly filled) and any gate block after it. The run picks up at the first stage that isn't recorded as **pass**, at the command after the last one recorded, or at a gate that hasn't been called; a failed stage comes back to its failure, not past it. Then check each stage against its sub-task: Done should mean the Record says **pass** and any gate it waits on is passed; In Progress is normal for a stage that's partly done. Show any other mismatch to the user to settle before you go on.
4. **Show where things stand:** one table, one row per stage: number, title, sub-task, status (done, in progress, failed, next, not started), then each gate and whether it's been called.

## 2. Each stage

1. **Start it.** Move the stage's sub-task to In Progress, assigned to the user. It stays In Progress for all of the stage's commands.
2. **Give the command.** Say the stage's number and title and what it proves (for its first command), then the next command exactly as the runbook has it, in a code block. Name any value the user must fill in and where it comes from. Then say what output to expect, in the runbook's words, and anything to blank out before pasting.
3. **Wait** for the output. Don't guess what it will be.
4. **Check it** against what the runbook expects: **pass**, **fail**, or **unclear**, with the reason in one line. For unclear, ask for the one extra thing you need (another command from the runbook, or more of the output).
5. **Record it** in the working copy's Record block for the stage as you go: which commands have run, their results, the time, and the named values the Record asks for, taken from the output (with secrets blanked). A partly filled Record is how a later session knows where the stage stopped.
6. **Next command, or close the stage.** Go one command at a time. When the stage's last command passes, mark its Record **pass** and comment on its sub-task (the result, the recorded values, and where the working copy is). Move the sub-task to **Done** only when its "Done when" is fully met: if that names a gate, the sub-task waits for the user to pass the gate (section 3).
7. **Before a merge or deploy command,** check what the runbook can't know in advance:
   - **Before merging a stack:** the stack holds exactly the PRs the runbook's stage names, no more (`gh stack view --short`; the merge takes every PR in it); every PR in it is open and mergeable; the latest run of every check on each PR's current head has completed successfully (a queued or running check blocks the merge, even when an older run passed); and the stack's base is current `main` (if not, the owning session rebases it first and CI goes green again).
   - **Before merging a release PR** (for example Release Please's): the stack it follows is merged; after `git fetch origin`, `git diff --name-only origin/main origin/<release branch>` shows only the release files (the user runs it; local refs don't update when GitHub merges or the release tool pushes) (if it shows code, the release branch was built on an older `main`: rebuild it on current `main` first); and the release PR's own checks pass the same way.
   - **Before a deploy:** the merges the runbook puts first are done, and the image or commit being deployed is the release commit (its build run is for that commit and succeeded).
   - **After a release publishes:** its release workflow run succeeded, including any tracker sync.
8. **On a fail:** stop. Record it, comment on the sub-task, leave it In Progress, and show the stage's rollback ("If it goes wrong") from the runbook. Wait for the user's decision: fix and retry, roll back, or stop the run.

## 3. Gates and pauses

- **At each gate,** show the stages it covers and their results, and ask the user to call it. Only an explicit "pass" counts. Record who decided and when in the gate block, then move to Done any sub-task that was waiting on this gate. Don't start a stage after the gate without it.
- **When the runbook says to wait** (for a deploy day, or until another stage is done in another environment), say so and stop.
- **When the user stops,** write where the run is at the top of the working copy, so any later session can pick up there.

## 4. Finish

When the last stage passes:
1. Fill in the run header's outcome in the working copy.
2. Comment on the rollout ticket: the outcome, each stage's gate, where the working copy and transcript are, and the runbook's **Afterwards** items.
3. Move the rollout ticket to Done once every sub-task is Done and the user agrees. Then check that every ticket under the epic is Done, except person-owned tasks (labelled `tracker.person_task_label`): those stay open with their owner, who gets a reminder in the 🙋 **Your turn** block when they're due, and the epic stays open until they're done (as `close-out-epic` step 6 says). For the rest: a release whose tracker sync failed, or a fix that shipped in another repo's commit, can leave tickets at `tracker.statuses.ready_for_release`. Close each leftover by hand with the version it shipped in, and say why in a comment.
4. **Update the build guides** once production runs the code. Find them from the epic: its `<EPIC> Build Guide.html` attachment or artifact link, the Artifacts table in its tech lead prompt, and any cross-epic guide the epic or its description names (a guide can cover several epics). For each one:
   - read the live version first (it may have changed since it was made, or belong to someone else who gave the user edit access);
   - mark what this rollout shipped in the guide's own words ("done" for the epic and its stories, "Live" for the screens it built, and so on), and update its counts;
   - show where deferred work went (the follow-up epic and standalone tickets from the epic's Close-out comment), and anything that changed from the plan;
   - leave every other epic's content as it is.

   Show the user what you'll change in each guide, then republish it to the same link, and comment on the epic with what was updated.
5. Show the **Runbook fixes** list, if it has anything, and offer to have the session of `deploy.runbooks.repo` fix the runbook in the repo.

## Report

Each turn is short: the stage and command, or the check and what you recorded. At a gate or a stop, a 🙋 **Your turn** line comes first, saying exactly what the user must decide.
