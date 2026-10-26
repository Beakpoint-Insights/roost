---
name: write-runbook
description: Write or rewrite an operational runbook in roost's recordable, gated format, with literal commands for each environment, a run record, pass/fail gates and a rollback, and keep it one to one with the rollout ticket's sub-tasks (one sub-task per stage, same number and name, checked both ways). Use when the user asks for a runbook, a rollout or migration procedure, or says an existing runbook doesn't follow our runbook practices.
---

# Write Runbook

**First, load the team config with `roost-config`.** Runbooks live in `deploy.runbooks.dir` in the `deploy.runbooks.repo` repo. If the config names a model runbook (`deploy.runbooks.model`), read it before writing and follow its shape. Follow every rule in `deploy.runbooks.house_rules` as well as the rules below.

## What every runbook has

1. **Header:** title with the ticket key, the ticket and epic, the audience ("whoever flips X in production"), and the namespace, workload and secret names the commands use.
2. **Preconditions:** what must be merged, deployed and verified first, each checkable.
3. **How to record this run:**
   - Copy the runbook to a working file so the template stays blank: `cp docs/runbooks/<file>.md ~/<key>-run-$(date +%Y%m%d).md`
   - Capture a transcript: `script -a ~/<key>-run-$(date +%Y%m%d).log`
   - A **run header** table (date and operator, environments touched, image tag, transcript path, outcome checkboxes).
   - A **status roll-up** table: every step, what it proves, done, result, evidence. Gate rows in bold. A `fail` in any gate stops the run.
4. **Stages,** each a series of numbered steps (P1, A1, B1 …) ending in a **gate**. Each step has:
   - what it proves, in one line
   - the exact command, single-line and pasteable
   - the expected output, literally
   - a **Record** block to fill in (done, result, the named values to copy from the output)
5. **Rollback:** the exact commands to undo each stage, and how to tell it worked.
6. **Afterwards:** what to check later, and where the filled-in record goes.

## Rules

- **Literal values, not instructions for building them.** Real hosts, client IDs, redirect URIs, namespaces and flag names, taken from `deploy.runbooks.config_sources`. Production gets its own commands; never "same as staging".
- **Secrets are never pasted.** Read them from the deployed secret (`deploy.secret_read`), or use a clear placeholder for the secret value only.
- **No helper scripts** for things the operator can do directly. One plain command per step.
- **Match the rollout.** If an epic has a rollout runbook, line the stages up with its steps and say which flag state each stage runs under and whether it emails users or writes data.
- **Check every command against the code:** CLI arguments, exit codes, config keys. Say in the report that you checked them but didn't run them, unless you did.
- **Read what starts each deploy before ordering anything.** Read the workflow files' `on:` triggers (the image build, the staging and production deploys, the release tool, any tracker sync) and any hosting platform's production branch (`deploy.frontend_host`), and state in the runbook what starts each deploy, naming the file. Don't assume a merge deploys anything.
- **Merge the release PR before building,** when `deploy.release_tool` opens one (Release Please does). Merging a repo's stack opens or updates its release PR. Merge it right after the stack, then build and deploy the release commit, so production runs the released version. Say what merging it starts by itself (a build, a tracker sync), and which of those to cancel.
- **Every command runs from a clean checkout.** No untracked local scripts, and no secret on the command line: read secrets at run time from a config file in the repo or the deployed secret, and pass them to containers with a bare `-e NAME`. If a step needs a script, commit it without secrets first.
- **Expected values come from the real config, not memory.** Read the deployed secret or settings file for hosts, ports and URLs (a pooler port and a direct port can differ), and give the value the operator will actually see.
- **Commands work in `team.shell`** (zsh by default). Keep `!` out of double quotes (set such values first in single quotes), and check each command pastes and runs as one line.
- **Merging a stack:** name the exact PRs the stage merges, and only those. Use `gh stack merge <top PR> --<vcs.merge_method>` (atomic); first check `gh stack view --short` lists exactly those PRs, since the merge takes every PR in the stack. When a release PR follows (`deploy.release_tool`), after it updates run `git fetch origin`, then check `git diff --name-only origin/main origin/<release branch>` shows only the release files (manifest, changelog, version) before merging it. Before it, check the stack's base is current `main`; if `main` has moved, the owning session rebases the stack and CI goes green first.
- **Alerts need data first.** Many metric tools only show a metric after its first data point, so an alert can miss the first failure on a fresh deployment. Put the alerts stage after production has run the new code and had traffic, and test every alert end to end, with a real event that reaches the notification channel.
- **Say what a gap between steps costs.** When steps should run close together (for example within an outside service's event retention window), say what is lost if they don't and what still covers it, so the operator can decide whether to pause.
- Plain language, no em dashes. Rewrite an existing runbook as one coherent document; don't append a changelog.

## Every stage is a sub-task

The runbook and the rollout ticket's sub-tasks list the same work, in the same order, one to one. Whoever runs the rollout can work from either and miss nothing.

- **Number the stages** 1, 2, 3 … in the order they run, across environments (for example "3. Staging: apply the database migrations", "7. Production: deploy"). Steps inside a stage keep their own numbers (3.1, 3.2 …).
- **One sub-task per stage,** titled exactly like the stage, number included. The stage's heading in the runbook ends with the sub-task's key: `## 3. Staging: apply the database migrations (PROJ-1234)`.
- **The sub-task's description** says what the stage proves, names the runbook section (path and heading), and gives the stage's gate as its "Done when". For a check that must pass before a deploy (a SQL query, a setting in an outside service, a secret), also put the exact command and the result that means "safe to proceed". Otherwise leave the commands in the runbook only, so there's one copy to keep right.
- **Nothing lives in only one place.** Work the rollout needs (merging the stacks, setting up alerts, turning on a flag, cleaning one up) is a stage, not just a sub-task. A stage the release doesn't need is cut from both.
- **Existing sub-tasks:** reuse them. Retitle and renumber one that covers a stage rather than adding a duplicate. A sub-task that matches no stage either becomes a stage, or comes off the ticket with the user's decision.
- Set Components on each sub-task.

**Check both ways before you finish:** list the stages and the sub-tasks side by side. Every stage has its sub-task with the same number and title, and every open sub-task on the ticket is a stage. Put that table in the report.

## Point the rollout ticket at the runbook

Comment on the rollout ticket with the runbook's path and branch (for example `docs/runbooks/workos-user-migration.md` on `PROJ-2729-…`, PR #543) and a one-line summary of its stages. Whoever runs the rollout starts from the ticket. When the runbook changes later, add a new comment saying what changed, rather than editing the old one.

## Report

Lead with what changed and whether any command was run. Then the stage-and-sub-task table, then anything the operator must decide or supply.
