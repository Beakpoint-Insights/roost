---
name: review-epic
description: Review a whole epic's code before it's released, in every repo it touches, against main. Each repo's session runs /code-review at high effort on everything the epic's stack changes, and the lead repo's session also runs /security-review, looking for what slice-by-slice reviews miss (how the slices interact, fixes layered on fixes, code that was never reviewed). Findings come back to one checkpoint for the user's decisions (fix now, ticket for later, skip), then go to the owning session. Use before release QA (build-epic calls it), before merging a big stack, or when the user asks "has this epic been reviewed?" or "review the whole epic". Run it from a separate orchestrator session, like run-slice.
---

# Review Epic

Slice reviews look at one slice against the slice below it, and bug fixes added after a slice's review often get none. Nothing looks at the epic as a whole, the way it will merge. This skill does, once, before release.

Talk to the repo sessions exactly as `run-slice` describes. You never review, edit or test any repo yourself.

**First, load the team config with `roost-config`.**

## Inputs

- **EPIC:** the epic's ticket key.

## 1. Know what was and wasn't reviewed

List every PR on the epic's stacks in every repo (the epic's **Release order** comment, or `gh stack`), and for each, how it was reviewed:

- GitHub reviews (`gh pr view <n> --json reviews`): Copilot, the Claude app, people;
- `/code-review` runs recorded in run-slice's state files (`<team.state_dir>/STORY.md`) or the stories' `run-slice checkpoint:` comments;
- none.

Mark the PRs that were never reviewed, and fixes made after a slice's review. The sessions should look hardest there.

## 2. Ask for the reviews

Send each session one message (they can all run at once):

- **The scope:** every change the epic makes in that repo: `main...<the top branch of the epic's stack in that repo>` when it stacks; without stacking, every PR of the epic's in that repo, merged or open (from the Release order comment), from the commit before the first one merged to the newest.
- **Run** `/code-review` at **high** effort, with the repo's `review_focus` if it has one. The lead repo's session (`planning.lead_repo`) also runs `/security-review`, since epics touch sign-up, keys, payments and data more often than not. If another repo holds server code, or has `apply_gate` (identity, network exposure and secrets live there), its session runs it too.
- **For a repo with `apply_gate`,** review the plans applied during the epic too: what was destroyed or replaced, what's reachable from outside, permissions wider than needed, and whether a fresh plan against each environment shows no changes.
- **Focus on what slice reviews miss:** how the slices interact end to end; fixes layered on fixes; secrets, tokens and authorization across the whole flow; data and migrations; concurrency; error paths and accessibility across the flow; duplicated code left between slices; tests that pass for the wrong reason.
- **Point it at** the never-reviewed PRs from step 1.
- **Grade every finding,** drop false positives (and say how many), and don't fix anything yet.
- **Report:** numbered findings, each with severity, `file:line`, the PR and story it came from, whether that code had been reviewed before, and what the session would do.

## 3. Checkpoint: the user decides

One combined list for every repo, bottom line first ("2 Important findings in never-reviewed code, 9 Minor"), with a recommendation for each: **fix now**, **ticket for later**, or **skip** (with why). Judge security findings the `triage-ticket` way. This is the skill's only stop.

## 4. Carry the decisions out

- **Fix now:** send each to the owning session, the way `run-bug` sends a fix: test-first, one commit per finding (signed, if `vcs.signed_commits`), on the epic's stack (a new branch on top), with a PR title that follows `vcs.pr_title`. Then the fix's own diff gets a quick `/code-review`, and its PR goes into the epic's Release order comment.
- **Ticket for later:** create the ticket under EPIC with Components, a "relates to" link to the story the code came from, and a description that stands on its own. `close-out-epic` decides later whether it stays or moves.
- Post one `review-epic:` comment on EPIC with the findings table and each decision, so the review is on the record.

## Report

Anything the user must do first, in a 🙋 **Your turn** block (leave it out when there's nothing). Then one line: "PROJ-2306 reviewed: 14 findings, 3 fixed, 6 ticketed, 5 skipped; PRs never reviewed before: 7." Then the findings table with each decision and its outcome.
