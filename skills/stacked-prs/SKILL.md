---
name: stacked-prs
description: Work with GitHub stacked pull requests (gh stack) in the team's repos. Put a branch on the right stack, commit, push and open its PR with the "Stacked on" banner, fix a merge conflict on the one branch that has it, and walk a stack bottom to top. Use whenever the user says "on the stack", "add it to the stack", "open a PR on the stack", "fix the conflict", or pastes GitHub's stacked-PR conflict steps.
---

# Stacked PRs

This team ships most work as a stack of pull requests managed with `gh stack` (`vcs.stacking: gh-stack` in the roost config). Each PR is based on the branch below it, so a mistake in one place shows up in every PR above it. Getting this right quickly matters more than explaining it.

**First, load the team config with `roost-config`.** This skill uses `vcs`, `repos` and `deploy`.

**With `vcs.stacking: none`,** there are no stacks: every branch starts from `main` and is its own PR against `main` ("Without stacking" in `roost-config`). Skip every `gh stack` step and "One deploy per stack", and publish a change this way instead, with the rules below, the commit and PR title rules, and the Release order comment as usual:

```bash
git switch -c <branch> origin/main        # or from the branch it needs, if it needs one
# commit (signed, if required)
git push -u origin <branch>
gh pr create --base main --title "…" --body "…"   # add "Waits for #<PR>." when it started from another branch
```

When the branch it started from merges, rebase it onto `main` (`git rebase --onto origin/main <that branch> <branch>`), force-push with lease, and drop the "Waits for" line.

## Rules that always apply

- **Pasted steps are the request.** If the user pastes instructions (for example GitHub's "Use the gh stack CLI to resolve conflicts" steps), do exactly those steps. Don't investigate first, ask for a go-ahead, or widen the scope.
- **Only touch the branch you were asked about.** Fixing one PR's conflict doesn't mean rebasing or force-pushing the whole stack.
- **Signed commits,** when `vcs.signed_commits` is true. Never pass `--no-gpg-sign`. If signing fails because it's blocked on the user (`vcs.signing_blocker`; errors like `vcs.signing_errors`), stop, say so in one line, and wait. Don't retry in a loop.
- **No worktrees and no side branches.** Work in the checkout that's already there. Stage your own files by path, never `git add -A`, because another session may be editing the same repo.
- **Report in one line when it went as asked.** For example "Pushed PROJ-2759 and opened #183 on the stack." Detail only when something didn't go as asked.

## Find where you are

Run these before creating a branch, opening a PR, or saying what's deployed:

```bash
git status --short
git log --oneline origin/main..HEAD | head -20   # commits not on main yet
gh stack view --short                            # this stack's branches and PRs, bottom to top
```

Code that isn't on `main` isn't running in staging or production. Don't reason about an environment from a branch.

## Add a branch on top of a stack

```bash
gh stack checkout <PR number or branch in the stack>
gh stack top                      # go to the top branch
gh stack add PROJ-1234-short-description
```

Branch names follow `vcs.branch_name`, starting with the ticket key. Each fix gets its own branch unless the user says otherwise.

## One deploy per stack

A stack holds the PRs of **one deploy** only. Merging a stack merges every PR linked into it, so a branch meant for a later deploy must never be linked into an earlier deploy's stack.

- **Before `gh stack link`,** read the branch's deploy in the epic's **Release order** comment (its **Deploy** column). Link it only into the stack whose PRs share that deploy.
- **The first branch of a new deploy starts a new stack.** Create it on the earlier deploy's top branch if it needs that code, but don't link it into that stack, and give its PR the banner `> Ships in Deploy <N>. Waits for Deploy <N-1> (#<PRs>) to merge.` Later branches of the same deploy stack on it as usual.
- **When the earlier deploy has merged,** rebase the whole new stack onto `main`, bottom to top: `gh stack rebase`, or from the top branch `git rebase --update-refs --onto origin/main <old base> <top branch>`, which moves every branch in it. Push every rewritten branch (force-with-lease), and retarget the bottom PR to `main`.
- **Before anyone merges a stack,** list exactly which PRs the merge takes (`gh stack view --short`) and check every one is in this deploy. If one isn't, unlink it first.

## Commit, push and open the PR on the stack

1. Commit (signed, if required), with a message that names the ticket. When `vcs.pr_title` is `conventional`, use a Conventional Commit, for example `fix(PROJ-1234): …`.
   The **PR title** follows `vcs.pr_title` too, for example `feat(PROJ-1234): API keys page on the managed-list pattern`. The repos' title checks fail on anything else ("PROJ-1234 backend (1/2): …" fails). With `vcs.merge_method: squash`, the title becomes the commit message.
2. Push: `gh stack push`.
3. Open the PR against the branch directly below it, never against `main`:
   ```bash
   gh pr create --base <parent branch> --title "…" --body "$(cat <<'EOF'
   > [!NOTE]
   > Stacked on #<parent PR number>.

   ## Summary
   …
   EOF
   )"
   ```
4. Link it into the stack on GitHub: `gh stack link <stack number> <new branch>`. Get the stack number from `gh stack view`. If `link` asks for the full list, give every PR in the stack, bottom to top.
5. Check it landed: `gh stack view --short` shows the new branch on top, and the PR's base is the parent branch.

If the user says "we're already on a PR", don't open another one: push and update the existing PR's title and description instead (`gh pr edit`).

### Cross-repo dependencies

Don't write dependency prose into PR descriptions ("the frontend still waits for this branch, because …"). Every PR in a stack ends up with one, and readers miss them. Instead:
- The epic has one **Release order** comment in the tracker that lists every branch and PR in deploy order, across every repo, with a **Deploy** column (which deploy ships it) and what each waits for. Whoever opens a PR adds it there (`run-slice` and the tech lead keep it current).
- **A PR in a repo with `depends_on` that can't ship until a PR in the repo it depends on is deployed** gets one banner line under the "Stacked on" note, linking that comment:
  `> [!IMPORTANT]`
  `> Ships after <that repo's name> #577 and #578 are deployed. Release order: <link to the epic's comment>.`
- PRs in repos that don't depend on another repo (no `depends_on`) carry no dependency note.

### Migrations need a deploy note

When `deploy.migrations_run_on_deploy` is false, staging and production don't run migrations on deploy (`deploy.migrations_note`), so a migration that only reached the local database is easy to forget. Whenever a branch adds a migration, make sure a deploy note covers it, and add one only if it's missing:

- **Where:** the epic's deploy ticket (its "Deploy …" Task, for example PROJ-2795). For a standalone bug, the bug's own ticket.
- **The note:** one **Migrations to apply** comment, listing every migration on the stack in order, with its context or module and the story or bug that added it. Update that comment when a migration is added; don't start a second list.
- **The steps:** a pre-deploy sub-task each for staging and production ("Before deploying: apply the database migrations"). Each has the back-up step and, for each context, `deploy.migration_apply`, where `$CONN` is read from that environment's deployed secret when the step runs (`deploy.secret_read`, as `write-runbook` does). **Never paste a connection string or password into the tracker**, in the sub-task or a comment. The step is done when `deploy.migration_verify`, with the same context and `$CONN`, shows them applied, so it checks the environment that was migrated. Create the sub-tasks once; later migrations go into the existing ones.
- A migration that only changes the model snapshot (no DDL) still goes on the list, marked "snapshot only", so the history matches.

### Evidence an agent can't attach

`gh` can't attach images to a PR. Put screenshots on the story's ticket (see "Attach a file" in the tracker adapter) and add a PR comment that lists them and links the story. Never pass this to the user.

## Fix a merge conflict

GitHub's own steps, which the user expects followed exactly:

```bash
gh stack checkout <PR number>
gh stack rebase
# fix the conflicts, then commit (signed, if required)
gh stack push
```

- Fix the conflict on the branch that **introduced** it. Fixing it on a branch higher up leaves the lower PR still conflicted.
- Then check that GitHub shows that PR as mergeable: `gh pr view <number> --json mergeable,mergeStateStatus`.
- If the PRs above it now conflict, and the user asked you to keep going, work up the stack one PR at a time, the same way. Otherwise report which PR conflicts next and stop.
- Stash and restore uncommitted work around a rebase without asking.

## Refresh local tracking

When the user asks to "refresh the local gh stack tracking", run `gh stack checkout <a PR in the stack>`. It pulls the stack's branches and tracking from GitHub. Don't use `gh stack sync` unless asked: it also rebases and force-pushes every branch.

## After pushing

- If CI runs on the PR, say so and give the PR link. Don't wait silently.
- If the user asked for an updated PR description, rewrite it as one coherent description of the branch, not a changelog of edits.
