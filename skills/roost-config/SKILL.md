---
name: roost-config
description: Load the team's roost config (which tracker, which repos and sessions, the local stack's commands, branching rules, deploy and design details) and the adapter notes for its tracker and test tool. Every other roost skill uses this first, before it reads or changes anything. Use it directly when the user asks "what does roost know about our setup?" or "which config is roost using?".
user-invocable: false
---

# Roost Config

roost's skills describe a way of working. Everything specific to one team (its tracker and project, its repos, its local stack, its branching and deploy rules, its design system) lives in one config file. Load it before doing anything else, and use its values wherever a skill names a config key.

**Read the config before any other call.** Don't send a tracker, GitHub or other tool call in the same batch as reading the config, and never guess a value it holds (a site, a cloud ID, a project key, a repo name). Wait for the config, then use its values.

## 1. Find the config

Use the first one that exists:

1. A path the user gave in this conversation.
2. The `ROOST_CONFIG` environment variable (`echo "$ROOST_CONFIG"`).
3. `.roost/config.yml` in the current directory or the nearest parent that has one (stop at the repo root).
4. `~/.claude/roost/config.yml` (often a link to the team's shared config in its private repo).

Read the whole file. Say in one line which file you're using, and its `team.name`, when the user asks, when it isn't the one they'd expect, or when more than one of these places has a config (for example `$ROOST_CONFIG` names one team's and `~/.claude/roost/config.yml` another's), so nobody runs one team's work on another's config.

**One machine, several teams.** A session outside every repo (an orchestrator) finds only `$ROOST_CONFIG` or `~/.claude/roost/config.yml`. To work for a team whose config isn't the one in `~/.claude/roost/config.yml`, start the session with `ROOST_CONFIG=<path to that team's config> claude`, or name the path in the conversation.

**Orchestrators record their config.** `run-slice` and `build-epic` write the config's path and `team.name` into their state file when a run starts. On a resume, if the config you loaded isn't the recorded one, stop and say which each is: the run continues on the recorded config once the user names it, or on the new one if they say so.

**If there's none,** stop: say roost has no team config yet and that `/roost:setup` makes one. Never fill a missing value in from memory, from the example config, or from another team's config.

**The config you found is the config.** Use its values as they are, even when they look made up: a config the user names may be the example one (`examples/config.example.yml`, the made-up Acme team), and that's their choice. Don't stop to ask whether it's "really" theirs, and don't check it against who the user seems to be (their email, signed-in accounts, other configs on the machine). If a value is wrong, the first call that uses it fails and says so; report that then.

**Then apply this machine's overrides for this team.** They hold only the values that differ on this machine (for example, a local database instead of the shared one). Overrides belong to one team, so another team's never apply:

1. `~/.claude/roost/local/<team.name>.yml`, if it exists. Use it, and ignore `local.yml`.
2. Otherwise `~/.claude/roost/local.yml`, if it exists, but only if its `team.name` is this config's `team.name`, or it has no `team.name` (the older form). Skip one that names another team. For the older form, say once that it applies to every team's config on this machine, and that moving it to `~/.claude/roost/local/<team.name>.yml` makes it this team's only.

The override's values win over the team config's:

- a mapping is merged key by key, so `stack.database.local` in an override changes only that key;
- any other value, a list included, replaces the team config's value whole;
- `repos` entries are matched by `name`, so an override can change one repo's keys without restating the others.

Use the merged result everywhere. When a value you act on came from an override, say so once, naming the file ("using this machine's database, from `local/Acme.yml`"), so nobody mistakes it for the team's.

## Which roost is running

Sessions can run different roosts: the installed plugin, or a checkout loaded with `claude --plugin-dir <checkout>` for that session only. Work out which one this session runs from this skill's own base directory, `<plugin root>/skills/roost-config`:

- **The version:** `version` in `<plugin root>/.claude-plugin/plugin.json`.
- **Installed or a checkout:** it's a checkout when `git -C <plugin root> rev-parse --show-toplevel` is the plugin root. Then add its branch, short commit, and whether it has uncommitted changes (`git -C <plugin root> status --porcelain`).

Write it as one line: "roost 1.0.0, installed" or "roost 1.0.0, checkout at ~/src/roost, main@66cdcd9, uncommitted changes". Give it when the user asks which roost or which version is running. Orchestrators record it (see `run-slice`).

## 2. Check it's supported

| Key | Supported now | Not yet |
|---|---|---|
| `tracker.kind` | `jira` | `github`, `linear` |
| `tests.kind` | `xray` | `repo-gherkin`, `none` |
| `vcs.stacking` | `gh-stack` | `graphite`, `none` |

If the config names one that isn't supported yet, stop and say which key and value, and that roost doesn't support it yet.

**Skills the config names must be installed.** When a step uses a skill the config names (for example `roadmap.skill`) and it isn't in this session's skill list, stop that step and tell the user which skill is missing and which plugin provides it. Don't look for its files on disk or do the step from memory: a fix that only works on this machine is worse than a clear stop. Carry on with steps that don't need it.

## 3. Read the adapter notes you'll need

In this skill's `references/` folder:

- `config-schema.md`: what every key means, and its default. Read it when a key's meaning isn't obvious from its name.
- `tracker-jira.md`: how to do each tracker operation in Jira (create, set a parent, edit a comment in place, attach a file, transition, link, search). Read it before any tracker change.
- `tests-xray.md`: how to read and update test scenarios in Xray, and what "automated" means. Read it before touching tests.

## How skills refer to the config

A skill writes a config key in backticks, for example `tracker.statuses.ready_for_release` or `stack.services`. Use the value from the config. A few names come up everywhere:

- **The project:** `tracker.jira.project`. Ticket keys look like `<project>-1234`; the skills' examples use `PROJ-1234`.
- **The repos:** the `repos` list. Each has a `name`, a `role`, an `order`, and a `session` name (for example "API session"). "Each repo, in order" means by `order`. A repo with `depends_on` waits for those repos' work and follows its `contract` to consume it.
- **The lead repo:** `planning.lead_repo`, where the tech lead plans, the plan and runbooks live, and the stack's owner usually runs. Default: the repo with the lowest `order`.
- **A repo's session:** the Claude session whose working directory ends in that repo's `name`.
- **The local stack:** `stack`. Its `services` are what "the stack answers" means; its commands start, inspect and migrate it. `stack.never` lists commands not to use, and `stack.test_data` says how to put data into it. A repo with `local_stack: false` (an infrastructure repo, say) neither runs on it nor uses it: leave the stack's instructions, checks and browser testing out of everything sent to its session.
- **Repos that change real infrastructure:** a repo with `apply_gate` (see below).
- **A repo's review focus:** its `review_focus`, or else `planning.review_focus`.
- **Person-owned tasks:** tickets under an epic labelled `tracker.person_task_label` (default `person-owned`). They're work no repo session can do, with a named owner and a "When" (before release, after release, or after a named slice). Never send one to a session, never move one out of its epic, and never count one as leftover work; remind its owner when its "When" arrives.
- **The state directory:** `team.state_dir`, where orchestrators keep their records. Default `~/.claude/roost/state/<team.name>/`, so two teams on one machine never share state files. Say which folder you're using the first time you read or write one.
  - **A run's record may be somewhere else.** When an orchestrator finds no state file for its ticket in this folder, before it treats the run as new or rebuilds it from the tracker, it looks for `<KEY>.md` in the other folders under `~/.claude/roost/state/` and in that folder itself. If one is there, stop: say where it is and which config it records, and carry on only once the user says which config the run uses.
  - **Older records.** Before per-team folders, a config without `state_dir` kept its records directly in `~/.claude/roost/state/`. When this team's folder is the default and that folder has state files of its own (`*.md`, not in a team's folder), say how many there are and ask the user which team they belong to. Move them into that team's folder only once the user says; never assume they're this team's, and never leave them unmentioned.

### The apply gate

A repo with `apply_gate` holds code that changes real resources when applied (OpenTofu or Terraform against a cloud account, for example), not code tested on the local stack. Its work isn't done when its PR merges; it's done when a reviewed plan is applied. Every skill follows this:

1. **The session plans, and posts the plan.** It runs `apply_gate.plan` and puts the output (or its summary of what's added, changed and destroyed, with the full output linked) in the PR. Every push that changes the plan gets a new one.
2. **Nothing is applied without the user.** No session runs `apply_gate.apply` on its own, against anything. The orchestrator stops at an **apply** checkpoint: it shows the plan's summary, anything destroyed or replaced first, and asks the user. With `apply_gate.who: user` (the default), the user applies it themselves; with `agent_after_approval`, the user may tell the session to apply that exact plan instead.
3. **Apply when `apply_gate.when` says:** `before_merge` (the default) applies the plan from the PR's head, so a failed apply is fixed on the same PR and `main` always matches what's applied; `after_merge` applies from `main` once the PR merges.
4. **Record it.** A comment on the story starting `apply:` with the date, who applied, the PR and commit, the plan's summary, and the result. Then a fresh plan should show no changes; anything else is a finding.

`deploy.runbooks.never_run_against` applies to every session, not only `pair-runbook`: a session never changes anything there itself. Reading (a plan, a describe, a list) is fine unless the user says otherwise.

When the config has only one repo, there's one session, no cross-repo handoff, and "each repo, in order" is just that repo.

## When you stop for the user

Every roost skill stops for the user at its checkpoints. End each stop with the exact next step, as a question that names the skill or phase it starts ("Next: `slice-handoff` for PROJ-2789, then the PROJ-2790 kickoffs. Go ahead?"), with your recommendation when there's a choice. The user should never have to work out what "keep going" will do.

**A stop for a blocker isn't a checkpoint.** When you stop because something only the user can fix is missing (a session that isn't open, a tool or connection this session doesn't have, a sign-in), say what's missing and what you'll do once it's there, as a statement: "Once both sessions are open, I'll pick up at slice 4." Don't ask whether to go ahead; being asked to do the work was the go-ahead. A decision the skill gives the user is different: if one is open (which artifact to build, where a doc goes), still put it to them, with your recommendation, so they can answer while the blocker is being fixed.

## The signed-in browser

Jira steps the MCP can't do (attachments, parent changes, comment edits) use an API token when `JIRA_API_TOKEN` is set, and need no browser (see the Jira adapter notes). Only without the token, or to file Xray tests without the Xray keys, do they use the user's signed-in browser (the Playwright MCP). Every session on the machine shares that one browser, and only one session can use it at a time.

- **"Browser is already in use":** another session holds it. Never kill the browser or its processes; that ends another session's work. Tell the user which step is waiting, and ask them to free it (finish or close the other session's browser work), then retry.
- **Checks that don't need anyone signed in** (opening a local prototype, a page on the local stack) use an isolated browser if one is set up (a second Playwright MCP server started with `--isolated`). If none is, and the shared one is busy, say plainly that the check wasn't done and why. Never present unchecked work as checked.

**A key a skill needs isn't set:** ask the user for the value once, use it for this run, and suggest adding it to the config. Don't invent it.
