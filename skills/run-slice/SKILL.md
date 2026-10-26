---
name: run-slice
description: Orchestrate one slice (story) from kickoff to done by driving the user's repo sessions (one Claude session per repo in the team's roost config, for example an API session and a UI session) over cross-session messages. Sends each repo's kickoff prompt from the tracker in order, has the stack's owner start the local stack, then loops through test verification, code review, fixes and exploratory testing, stopping for the user's decisions. Never edits any repo itself. Picks up where a stopped run left off, from GitHub, the tracker and its own state file, and answers "where are we on PROJ-X?" with a short table, read-only, from a clean session. Use when the user says "run slice PROJ-X", "drive this slice", "pick up PROJ-X where we left off", "kick off the next slice", or asks where a slice or epic stands. Run it from a separate orchestrator session, not from inside any of the repos.
---

# Run Slice

You coordinate. Other Claude sessions do the work, one per repo in the config's `repos` (for example the **API session** and the **UI session**). You never edit, build or run tests in any repo yourself. Everything happens through `SendMessage`.

**First, load the team config with `roost-config`.** This skill uses `repos`, `stack`, `tracker`, `tests`, `vcs`, `planning.review_focus` and `team.state_dir`. "Each repo, in order" means the `repos` list by `order`.

## Inputs

- **STORY:** the slice's ticket key.
- A session for each repo the story touches must already be open. If one isn't, ask the user to open it and stop.

Every run starts with **step R (resume check)**, even a first run, so stopping and restarting is always safe.

If the user only asks where things stand ("where are we on PROJ-X?", "what's left?"), use **Status** below and stop there.

## Status: "where are we?"

Read-only. Send no messages, start nothing, change nothing. It must work from a fresh session with no memory of earlier runs, so use only GitHub, the tracker and the state file (step R, items 1 to 4).

**For a story,** one table and one line. Nothing else. One kickoff row per repo the story touches, in order:

| Step | State | Evidence |
|---|---|---|
| Backend kickoff | ✅ Done | #571, checks pass |
| Frontend kickoff | 🔄 In progress | `PROJ-2788-frontend`, no PR yet |
| Tests verified | ⏳ Remaining | 2 of 5 tests Done |
| Code review | ⏳ Remaining | |
| Fixes | ⏳ Remaining | |
| Exploratory testing | ⏳ Remaining | |
| Slice done | ⏳ Remaining | |

**Next:** finish the frontend kickoff (UI session), then check.

The steps are always these, in this order: the kickoffs, then the same five. Name each kickoff row by its repo's `kickoff_title` without the repo name in brackets. "Evidence" is one short fact a person can check: a PR number, a branch, a count, a ticket key.

**Always show the table, even when you can't read everything.** If a step's state can't be told (a source couldn't be read, or nothing records it), mark that row ❔ Unknown rather than guess.

Under the table, **at most two lines**, no bullet lists:
- one line naming everything that couldn't be read, together: "Couldn't read Jira, GitHub or the state file from this session."
- one line starting **Next:** with the single next action, in one sentence.

**The table is the first thing in the reply.** Nothing above it: no greeting, no summary, no apology.

Don't replace the table with an explanation, don't explain why a source was unreadable, and don't offer to start or resume work; the user asked where things stand.

**For an epic,** first one row per story, in the epic's story order, then the story table above for the one in progress:

| Story | Slice | State |
|---|---|---|
| PROJ-2787 | Free plan at sign-up | ✅ Done |
| PROJ-2788 | API key on Get started | 🔄 Frontend kickoff |
| PROJ-2789 | API keys page | ⏳ Not started |

A story is ✅ when it's at `tracker.statuses.ready_for_release` or later (or `done`, if the config has no ready-for-release status); 🔄 when any repo has a branch or the run's state file exists; otherwise ⏳.

## R. Resume check: where is this slice?

Work out the slice's real state before sending anything. Reading is fine; you still change nothing in any repo.

1. **Your own record.** Read the state file `<team.state_dir>/STORY.md` if it exists. It holds what only you know: the sessions found, each step's outcome, and the user's decisions at checkpoints. It's a record, not the truth: check it against steps 2 to 4. If the file isn't there (another machine, or it was cleaned up), read STORY's comments that start with `run-slice checkpoint:` instead; a checkpoint comment also means the check before it (tests and code review) ran.
2. **The kickoff comments** on STORY name each repo's branch (for example `PROJ-2788-backend`). For each branch, in that repo's `github`:
   ```bash
   gh pr list -R <repo.github> --head <branch> --state all --json number,state,isDraft,url
   gh pr view <number> -R <repo.github> --json statusCheckRollup
   ```
   A repo's side is **done** when its PR exists on the stack and its checks pass, and, for a repo with `apply_gate`, its plan is applied and recorded in an `apply:` comment on STORY (see "The apply gate" in `roost-config`). A branch with no PR means that side started and didn't finish.

   **Judge checks by each check's newest completed result** on the PR's current head. A run that a newer push cancelled is harmless, and a re-run still in progress isn't "pending" when the same check already passed: report it as "green; a re-run is in progress". If the list shows only the unfinished entry for a check (a re-run of the same job can replace its earlier result), call that check pending. `gh pr checks` lists cancelled and re-run entries as pending, so don't use it to decide. Before anything is **merged**, use the stricter rule: the latest run of every check on the current head has completed successfully, and a queued or running check blocks the merge.
3. **The tracker:** STORY's status, its linked tests' labels and statuses, and any tickets already created from this slice (linked "relates to"), so they aren't filed twice.
4. **The stack:** whether every `stack.services` URL answers (`curl -s -o /dev/null -w '%{http_code}' <url>`). Skip this when every repo the story touches has `local_stack: false`.

Then tell the user what you found and where you're picking up, in one short table, and carry straight on. Being asked to run the slice is the go-ahead; don't ask for another. Stop only for a real blocker: a session that isn't open, two candidates for one repo, a refused message, or a resume that would act again on decisions the user may have changed (below).

| Step | State | Evidence |
|---|---|---|
| Backend kickoff | Done | #571, checks pass |
| Frontend kickoff | Not started | no `PROJ-2788-frontend` branch |

Pick up at the first step that isn't done:
- **A repo started, not finished:** ask its session to continue from its branch, with its kickoff comment again for context. It decides what's left from the branch and the plan.
- **A repo done:** go on to the next repo in order (after getting the stack ready, if a later repo depends on it).
- **Every kickoff done:** start at step 2 (Check). Test verification and code review are safe to run again.
- **Mid-checkpoint or mid-fix:** use the decisions in the state file. Show them to the user before acting on them again, since they may have changed their mind.

A session opened fresh after a stop knows nothing about this run. Every message you send already stands alone, so that's fine; but say in the first message that you're resuming STORY at a given step.

## Migrations

When a session's report (or its branch) adds a database migration, and `deploy.migrations_run_on_deploy` is false, make sure the epic's deploy ticket covers it, as `stacked-prs` describes: the **Migrations to apply** comment and the staging and production pre-deploy sub-tasks. Add or update them yourself if the session didn't. Check the stack's migration files against the list; don't rely on the report alone.

## Keep the state file current

After every step and every checkpoint, update `<team.state_dir>/STORY.md`:
- the session names and refs, and the directory each reported
- each step: done, its outcome, PRs and commits from the session's report
- each checkpoint: the list shown and the user's decisions, word for word
- tickets you created

Write it as you go, not at the end, so a stop at any point loses nothing.

The state file lives on this machine only. So that Status works anywhere, also post each **checkpoint's decisions** to STORY as a comment starting with `run-slice checkpoint:`, with the decisions table. Status and the resume check read those comments when the state file isn't there.

## 0. Find the sessions

1. `ListAgents` to see the other sessions on this machine.
2. Don't trust names (they change, and two can look alike). Send each candidate:
   > Connectivity check from the run-slice orchestrator: reply with your working directory (`pwd`) and whether you're busy, then carry on as before.
3. A session whose directory ends in a repo's `name` is that repo's session. If there are two for one repo, or none for a repo the story touches, ask the user which to use.
4. Note each session's name and ref for the rest of the run.

If a send comes back held or refused (a `[Cross-session delivery notice]`), tell the user that session needs to accept messages, and stop.

## How to talk to the sessions

- **One instruction per message, fully self-contained.** The receiver reads it literally: no "as discussed", and no `@file` references, which attach nothing. Paste the text itself.
- **First line says what it is,** for example "run-slice: backend kickoff for PROJ-2788". The user sees that line as the preview in their IDE.
- **Ask for a report in this form** at the end of every instruction:
  > When you're done, reply to the orchestrator with: **Status** (done / done with concerns / blocked), **Branch and PR**, **Commits**, **Tests run** (name and pass/fail counts), **CI** (each check's newest completed result), **Concerns** (everything you noticed, including things that look unrelated), and **Needs from the user** (anything only they can do). Every claim about the code or data cites its `file:line`, or the query you ran and its result; write "unknown" for anything you didn't check, never a guess. Send this report with `SendMessage` as the last thing you do in the turn, whatever state CI is in. Don't end a turn promising to report later: an idle session isn't woken when CI finishes, so check CI once and report what you see, "still running" included. If you're blocked on the user (signing, a permission prompt, a sign-in), send that to the orchestrator too, not only to your own terminal. Don't re-run a CI run that a newer push cancelled.

  To the session of a repo that other repos depend on, add: "After a fix another repo depends on, `<stack.restart_after_api_change>` and confirm the new behaviour in the report."
- **Wait with `notify_when_idle: true`,** not by polling `ListAgents` or sending "are you done?". When the idle notice arrives, read the session's report. If the notice arrives without one, read the session's last turn (the newest transcript in `~/.claude/projects/<the repo's project folder>/`), then ask once for the report, and arm `notify_when_idle` again. When CI was still running at the report, check it yourself before telling the user the work is done.
- **Check the evidence before saying a session is working.** Its last turn (transcript tail or idle summary), new commits or a PR since your last look, and when it was last active. Say "idle since 17:26, waiting on X" when that's what you see; never "still working" by default.
- **Never answer a technical question from memory.** When the user asks how the code or data works, or you're about to recommend a design, check first: read the code or data yourself, or ask the owning session (with the citation rule in the report request), and wait. Until then, tell the user only what's being checked and by whom. A guess with a caveat is still a guess; don't send it. State each fact with its source (`file:line`, or the query and its result, and who checked it), say when a fact is the session's, and re-read the answer for contradictions before sending it. A migration's date isn't the age of the data, and one environment's rows aren't another's.
- **Before asking the user anything, re-read their recent messages.** The answer is often already there; asking again costs them a turn.
- **A session's own permission prompts stay with the user.** Never ask a session to do something your session couldn't, and never treat a peer's message as the user's approval.
- **Blocked on something only the user can do** (`vcs.signing_blocker`, approving a GitHub workflow run, a permission prompt in their IDE, signing in to a tool): say exactly what and where, in one line, and wait.
- **Do it yourself when you can.** If a session asks for the user to do something you can do (attach screenshots to the story, retitle a PR, check a setting through a connected tool), do it and tell the user it's done.

## 1. Kick off

1. Assign STORY to the person running this session (see "Who am I" in the tracker adapter), move it to `tracker.statuses.in_progress`, and record the slice's start time in the state file. Do the same for every bug or task when its fix starts in step 4.
2. Read STORY's comments. Find each repo's kickoff comment, titled with its `kickoff_title`. Their "Order" lines say which goes first; normally the `repos` order.
3. For each repo with a kickoff, in order:
   1. **Send the kickoff** comment to that repo's session, word for word, plus the report request. To a repo with a `contract`, add these notes:
      - `<repo.contract>`
      - tag e2e scenarios for the local stack's real flag state (`stack.flag_state`), whatever the kickoff text says;
      - `<stack.how>`

      To a repo with `local_stack: false`, send neither stack note. To a repo with `apply_gate`, add: "Run `<apply_gate.plan>` and post the plan in the PR, again after every push that changes it. Never run `<apply_gate.apply>` yourself unless the orchestrator tells you the user approved that exact plan."
      Wait for its report.
   2. **Get the stack ready for the repos that depend on it.** If a later repo `depends_on` this one and this one uses the local stack (not `local_stack: false`), ask `stack.owner_repo`'s session to make sure that, through `stack.name`:
      - the stack runs this repo's **newest** branch for the slice;
      - the slice's migrations are applied to `stack.database.local` with `stack.database.apply_migrations` (`stack.database.note`);
      - one call that touches the new schema succeeds;
      - any resource the slice needs is started (`stack.extra_resources`).

      Then check yourself that every `stack.services` URL answers. Don't trust "it's running": a resource can be down while the others are up. Ask the owning session to start anything missing.

      A repo with `local_stack: false` isn't run on the stack: for one with `apply_gate`, the apply checkpoint (next) is what makes its work ready for the repos that consume it.
   3. **Apply checkpoint,** for a repo with `apply_gate`, once its PR's checks pass and its plan is posted: follow "The apply gate" in `roost-config`. Show the user the plan's summary, with anything destroyed or replaced first, and stop for their decision. When it's applied, record the `apply:` comment on STORY and check a fresh plan shows no changes. A later repo that consumes what this one creates (its outputs, a cluster, a role) starts only after the apply.

      With `apply_gate.when: after_merge`, the plan can't be applied yet: hold this checkpoint until the PR has been through steps 2 to 5 and the user has merged it (step 6), then apply from `main`. Repos that consume its outputs start after that apply.
   4. **After each kickoff:** check the new PR's title follows `vcs.pr_title` (retitle it yourself with `gh pr edit` if not), and add it to the epic's **Release order** comment with its deploy (see `stacked-prs`). If it's the first branch of a later deploy than the branch below it, check it isn't linked into that branch's stack (`stacked-prs`, One deploy per stack).
4. **Before telling the user to merge,** check every repo with `apply_gate` and `when: before_merge` has its apply recorded for the PR's head; then list exactly which PRs the merge takes (the PRs linked into the stack, from `gh stack view --short`) and check each one belongs to this deploy. Name them in the message. Separately, check any other open PR whose base is a branch of this stack is unlinked and belongs to a later deploy (`stacked-prs`, One deploy per stack).

If a story has no kickoff for a repo, skip that repo. If a session reports **blocked**, stop and tell the user.

## 2. Check

Send these, then wait for every report:

- **The session of the repo that holds the e2e suite** (the one with `e2e` in the config), or, when the config has none, the session of the repo that owns STORY's work: "Use the verify-slice-tests skill for STORY. Don't carry out any split until the orchestrator tells you the decision." Skip this when STORY has no linked tests (retired ones don't count) because no suite can prove its work before release (a docs slice, for example). Instead, ask that repo's session to check each of STORY's acceptance criteria against its PR (the build and the preview), one row per criterion with its evidence.
- **Manual tests** linked to STORY (`tests.manual_label`), once the work they check is in place: send each to the session of the repo that owns that work, with the test's description, to run what it can read-only and record the run as the Xray adapter notes say ("Manual tests"). It runs nothing that changes a shared or production resource, and nothing in `deploy.runbooks.never_run_against`: those steps go to the user as 🙋 **Your turn** actions, and the session records the run from the user's answer. Skip tests with `When: after release`.
- **Every session the slice touched:** "Run /code-review on every change in this stack compared with `main`, with a focus on `<the repo's review_focus, or planning.review_focus>`. Report the findings; don't fix anything yet." To the session of a repo with `apply_gate`, add: "Review the posted plan too, not only the code: anything destroyed or replaced, public exposure, and permissions wider than the change needs."

## 3. Checkpoint: the user decides

Give the user one combined list, bottom line first ("2 tests need a decision, 5 review findings, nothing failing"):

| # | From | Item | Recommendation |
|---|---|---|---|
| 1 | Tests | PROJ-XXXX: split proposed | Split as proposed |
| 2 | API review | … | Fix now |
| 3 | UI review | … | Ticket for later |

Recommend one of: **fix now**, **ticket for later**, or **skip** (with why). **Recommend "fix now" only for two kinds of finding:** anything this slice introduced (in its code, tests, data changes, docs or behavior), and anything, introduced here or not, that stands in the way of the story's or the epic's goal (its acceptance criteria, a security or data-loss risk, or a problem the slice's own change exposes). Everything else, such as older bugs the review happened to read and minor polish, is "ticket for later" unless the user chooses otherwise. Mark each row "introduced here", "blocks the goal" or "older". Without this rule the loop doesn't end: every review of new fixes finds something new, and each fix adds code for the next review to find. For security findings, use the `triage-ticket` way of judging them: is it real, who could exploit it, how bad. Then wait for the user's decisions.

**Everything a session reported becomes a row:** every finding, concern or odd thing in any report since the last checkpoint (pre-existing lint errors, a resource that failed to start, a flaky test), not only the review findings. Nothing stays only in a session's report, where the next slice can't find it.

The `run-slice checkpoint:` comment uses one fixed table, so later steps can check it: **#**, **Item**, **Key** (the ticket, once there is one), **Decision**, **Outcome**. Fill **Outcome** as each item is carried out: a commit or PR for "fix now", a ticket key for "ticket for later", a reason for "skip". Say where deferred work goes in the table ("with PROJ-2809"), not only in prose.

## 4. Fix

- Send each "fix now" item to the session that owns the code, test-first, one commit per item, pushed on the stack (`stacked-prs`).
- An item that needs more than one repo: write each repo's part with `cross-repo-handoff` and send them in `repos` order. Send a dependent repo's part only after the repo it depends on reports done and the stack is restarted.
- Tell the e2e repo's session the split decisions, so `verify-slice-tests` can carry them out.
- "Ticket for later" items: create the tickets yourself. Each gets the **epic as its parent** (set at creation; see the tracker adapter for fixing a parent later), Components when the config requires them, and a "relates to" link to STORY.

## 5. Explore

Skip this step when the slice changes no UI (its story names no prototype screen), or the config has no e2e repo: its tests, its acceptance criteria and, for a repo with `apply_gate`, the fresh plan after the apply, are its checks. Otherwise, ask the e2e repo's session to do exploratory testing of **this slice only**, using `release-qa` steps 3 and 4, after loading the data the slice's screens need with `stack.test_data` if the config has it (local stack only): charters from STORY's prototype screen and states, in a real browser, filing only bugs it reproduced, as Bugs under the epic with Components set, each behaviour bug with the test that would catch it (`release-qa` step 4 says how). It shouldn't run the whole e2e suite or give a release call.

New bugs go back to step 3 for the user's decision, then to `bug-bash` in the session that owns each one.

## 6. Done for this slice?

Loop through steps 2 to 5 until all of these are true:
- `verify-slice-tests` shows every test automated, passing and done, or split with the user's approval, and every manual test (`tests.manual_label`) done on a passing `manual run:` comment, except those whose description says `When: after release` (see "Manual tests" in the Xray adapter notes). For a slice with no tests because no suite can prove its work before release, every acceptance criterion is checked on its PR, with evidence.
- A test created for an exploratory bug the user deferred may stay open and unlabelled: it's automated with that bug's fix, not in this slice. List it in the slice-done comment's **Left open** table with the bug and where the bug went.
- Every review finding is fixed, ticketed or skipped by the user.
- Every exploratory bug is fixed or deferred by the user.
- Every PR on the stack for this slice is pushed and its checks pass.
- Every repo with `apply_gate` has its plan applied and recorded for its PR's current head (or, with `when: after_merge`, for the merged commit), with a fresh plan showing no changes ("The apply gate" in `roost-config`). A fix in step 4 or a Copilot fix that changes the plan after an apply sends that repo back to the apply checkpoint (step 1) for the new plan; an earlier apply doesn't count.
- Every PR for this slice has had a **Copilot review**, and every Copilot thread has an outcome: accepted with its fix commit, declined with a reply saying why, or older and ticketed. As soon as a slice's PRs are pushed, without waiting for CI, send each owning session `references/copilot-review.md`, word for word with the PR numbers filled in, and wait for its table. File the "older" threads as tickets yourself (epic as parent, Components, "relates to" STORY). Accepted fixes count as fixes made since the slice's code review, so the next bullet's review covers them.
- The fixes made since the slice's code review were reviewed too: each session ran `/code-review` on just the commits after the review in step 2, and each finding is fixed or decided by the user. When you send that review, tell the session to report findings without fixing anything yet, identifying findings those fixes introduced or that stand in the way of the story's or epic's goal, and marking the rest as "older" for the checkpoint. Route all findings through step 3 using its recommendation rule, and carry out only the fixes the user approves in step 4. Review any resulting fixes in the same way. The slice is done when the latest fixes have been reviewed and every finding is fixed, ticketed or skipped by the user.

Before calling it done, **reconcile the record**:
- every checkpoint row has its Outcome;
- a wide search finds no ticket from this slice that isn't linked to STORY: everything created since the slice's start time whose parent is the epic or whose text mentions STORY, except person-owned tasks (see `roost-config`) and Xray Preconditions (see the Xray adapter notes). The start time is the one in the state file; when there isn't one (a resumed run on another machine), use the earlier of STORY's first kickoff comment and its first move to In Progress, and record it. Link any that belong, with the epic as parent and Components set.

Then:
1. Comment on STORY with the final state: the PRs, the tests and their status, tickets created for later, and bugs filed. End the comment with a **Left open** table (key, summary, where it goes: next slice, before release, or later), which `slice-handoff` reads and checks. Mark the state file's run as finished.
2. Run `slice-handoff` with STORY as the finished slice and the next story in the epic's order as the next one. It sorts what's left over, checks the whole epic's tests, and brings the next slice's kickoffs up to date.
3. **Checkpoint: ask the user** whether to start the next slice, in the same message as `slice-handoff`'s sorting table. Never start it on your own. When `build-epic` is running this slice, skip the question: the user's answers to the sorting table are enough, and `build-epic` starts the next slice.

## Progress updates while sessions work

Whenever you've sent work to a session and are waiting on it (a kickoff, fixes, exploratory testing, a rebase), give the user a short update every 5 minutes. Do this without being asked; the user shouldn't have to request it. Every update, scheduled or not, follows the update prompt below.

- **Schedule it** with `CronCreate`, every 5 minutes, recurring, as soon as you send the work. Its prompt is the update prompt below, with `{STORY}`, `{EPIC}`, `{SESSIONS}`, `{LOG}` and `{STATE_DIR}` filled in and everything else word for word, so every scheduled run follows the format without rereading this skill. Tell the user once that updates are on and that "stop" ends them.
- **Each update is read-only.** Don't message the sessions to ask how they're doing. Check only what you can see (the update prompt lists it). If the config has `stack.telemetry`, read it from `stack.owner_repo` with `stack.telemetry.logs` and `stack.telemetry.traces` (`stack.telemetry.note`): report only what's new since the last update, group repeats with a count, and flag anything that looks like a bug in this slice or a problem with the stack. Errors no session has mentioned are worth the user's attention.
- **Log skill gaps** you notice in `<team.state_dir>/lessons.md` (date, slice, what happened, skill affected, possible change).
- **Stop the schedule** (`CronDelete`) when nothing is outstanding: every session you sent work to has reported, the slice reaches a checkpoint that needs the user, it's done, or the user says stop. Arm it again when you next send work.

### The update prompt

```
roost progress update for {STORY} (epic {EPIC}). Read-only: don't message any session.

Check the evidence first: each session's transcript tail and last-activity time ({SESSIONS}), new commits on the slice's branches, each PR's checks and mergeStateStatus, open review threads, whether every stack.services URL answers, the stack's telemetry if the roost config has stack.telemetry, and any reports or idle notices received. Never report "working" without that check.

Then write exactly one of these three updates. Choose in this order: YOUR TURN if anything needs the user (new, or still unresolved from an earlier update); otherwise STALLED if work is stalled; otherwise moving.

1. Nothing needs the user. A level-4 heading, then ONE plain line. No bold, no tables, no bullets.

   #### 🟢 HH:MM · {STORY} · moving
   One plain sentence on what changed, for example "#603 CI 8/11 · 2 Copilot threads being fixed."

2. Something needs the user (a decision, a sign-in, a credential, a production query or change). Start with a level-2 heading, put the actions first as a numbered list, then at most two lines of context. Also send a PushNotification whose single line starts with the action.

   ## 🙋 YOUR TURN · HH:MM · {STORY}
   1. **The action, bolded.** Exactly what to do and where, for example `! aws sso login --profile X`.
   2. ...
   One or two plain lines of context: why the action is needed and what's waiting on it. Nothing else; status details (checks, commits, other PRs) go in the log line.
   For example: "The API session can't run its tests until you sign in. The UI session is waiting on it."

   Use this heading for nothing else. While anything in it is unresolved, repeat this block in every update, showing only what's still open.

3. Stalled: no session activity and no commits for 15+ minutes while work is outstanding. Start with:

   ## ⚠️ STALLED · HH:MM · {STORY}
   Who stalled, since when, and the evidence (last transcript activity time, last commit).

Rules for all three:
- The update is the whole reply: nothing before or after it, and no explaining what you left out.
- Lead with the answer; one line per fact; plain words, no jargon.
- Every heading carries the current time (HH:MM, local) and {STORY}: first in the moving heading, right after the label in the other two.
- Don't paste earlier updates under the new one; the log file keeps the history.
- Append one line per update to {STATE_DIR}/{LOG}-updates.md: "- HH:MM · {STORY} · what's happening · what's new".
```

`{LOG}` is the story's key when `run-slice` runs on its own, and the epic's key when `build-epic` runs it (`build-epic` keeps one log for the epic). `{SESSIONS}` names each session you sent work to.

### Examples

Nothing needs the user:

```markdown
#### 🟢 13:05 · PROJ-2789 · moving
#603 CI 8/11 · 2 Copilot threads being fixed.
```

Something needs the user (and a PushNotification: "Run aws sso login --profile beakpoint-dev in the API session"):

```markdown
## 🙋 YOUR TURN · 14:10 · PROJ-2789
1. **Sign in to AWS in the API session.** In its terminal, run `! aws sso login --profile beakpoint-dev`.
2. **Approve the workflow run on #604.** Open the PR's Checks tab and choose "Approve and run".
The API session is blocked on the expired AWS session; the UI session is waiting on its endpoint.
```

Stalled:

```markdown
## ⚠️ STALLED · 13:40 · PROJ-2789
The UI session, since 13:20: its transcript was last active at 13:19 and its last commit (a1b2c3d, "test: create dialog") was at 13:12. The frontend kickoff for PROJ-2789 is still outstanding.
```

## Report to the user

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then lead with where the slice is ("PROJ-2788: backend done, frontend running"), then a short table of what each session last reported. Keep a running status table during the run, one column per session:

| Step | API session | UI session |
|---|---|---|
| Kickoff | done, #NNN | running |
