# roost config schema

A team's config is one YAML file. A machine can override some of its values in `~/.claude/roost/local/<team.name>.yml` (see "Machine overrides" at the end). `examples/config.example.yml` in the roost repo is a complete example to copy. Keys marked *optional* can be left out; the skills then use the default, or skip what depends on them.

## `version`

Always `1`.

## `team`

| Key | Meaning |
|---|---|
| `name` | The team or company name. |
| `product` | The product's name as customers see it. Used in roadmap and prototype wording. |
| `state_dir` | *Optional.* Where orchestrator skills keep state files and update logs. Default `~/.claude/roost/state/<team.name>/`. State files are named by ticket key, so two teams on one machine need different folders: leave this out, or give each team its own. |
| `drafts_dir` | *Optional.* Where drafts for the user (prototypes, prompts) are saved. Default `~/Downloads`. |
| `shell` | *Optional.* The shell commands must paste into, for example `zsh`. Default `zsh`. |

## `tracker`

| Key | Meaning |
|---|---|
| `kind` | `jira`. (`github` and `linear` aren't supported yet.) |
| `jira.site` | The Jira site, for example `acme.atlassian.net`. |
| `jira.cloud_id` | The site's cloud ID, for the Atlassian MCP tools. |
| `jira.project` | The project key, for example `PROJ`. |
| *(environment)* | Not in the config, because they're secrets: `JIRA_EMAIL` and `JIRA_API_TOKEN` let skills change parents, edit comments and upload attachments without a browser; `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` let them read and write Xray tests through its API. |
| `jira.epic_issue_type_id` | *Optional.* The Epic issue type's ID, when creating epics needs it. |
| `statuses.todo` / `in_progress` / `done` | The workflow's status names. |
| `statuses.ready_for_release` | *Optional.* The status for work that's merged and waiting to ship. Leave it out if merged work goes straight to `done`; skills then move tickets to `done` at that point and skip the release-time checks for it. |
| `statuses.wont_do` | *Optional.* The status for a ticket closed without a fix. |
| `components_required` | *Optional.* `true` if every ticket needs Components set. Default `false`. |
| `person_task_label` | *Optional.* The label on a person-owned task: epic work no repo session can do (a PR to another company's repo, a video, a partner conversation). Build and close-out skills leave these to their owner. Default `person-owned`. |

## `tests`

| Key | Meaning |
|---|---|
| `kind` | `xray`. (`repo-gherkin` and `none` aren't supported yet.) |
| `automated_label` | The label for a test whose every scenario is automated and passing. Default `automated`. |
| `manual_label` | *Optional.* The label for a test that's run by hand on purpose, once, against a real environment, and closes on a recorded run instead of automation (see "Manual tests" in the Xray adapter notes). Leave it out to allow no manual tests. |
| `xray.test_link_type` | The link type between a test and its story: `name`, `id`, and the `outward`/`inward` wording. Default `Test` ("tests" / "is tested by"). |
| `xray.panel_test_id` | *Optional.* The Xray panel's test id in the Jira issue view, for browser steps. |

## `repos`

A list, one entry per repo a story's work can touch. One entry is fine.

| Key | Meaning |
|---|---|
| `name` | The repo's folder name. A session whose working directory ends in it is that repo's session. |
| `github` | `owner/repo` on GitHub. |
| `role` | A short word for what it holds: `backend`, `frontend`, `mobile`, `infra`, … |
| `session` | What to call its session in messages, for example "API session". Default "`<name>` session". |
| `ide` | *Optional.* Where the session usually runs, for the user's benefit. |
| `order` | The order work goes in within a story. Lower goes first. |
| `depends_on` | *Optional.* Repos whose work this one consumes. Its work waits for theirs. |
| `contract` | *Optional.* How this repo consumes the work of the repos it depends on, as an instruction to its session (for example "regenerate the API client against the running API; never check out the API repo"). |
| `kickoff_title` | The title of this repo's kickoff comment on a story. Default "Kickoff (`<name>`)". |
| `branch_suffix` | Added to the story key for this repo's branch (`PROJ-1234-<suffix>`). Default the `role`. |
| `owns` | What kind of change belongs in this repo, in words, for deciding where work goes. |
| `tests` | The kinds of tests this repo has and where they live, in words. |
| `local_stack` | *Optional.* `false` for a repo that doesn't run on or use the local stack (an infrastructure repo, for example): skills leave the stack's instructions, checks and browser testing out of its work. Default `true`. |
| `review_focus` | *Optional.* What `/code-review` should focus on in this repo, instead of `planning.review_focus` (for example "IAM least privilege, public exposure, state and secrets, destroy or replace in the plan"). |
| `apply_gate` | *Optional.* For a repo whose changes are applied to real resources (OpenTofu, Terraform): `plan` (the command that produces the plan, for example `tofu plan -out=tfplan`), `apply` (the command that applies it), `who` (`user`, the default, or `agent_after_approval`: the session may apply a plan the user approved), and `when` (`before_merge`, the default, or `after_merge`). See "The apply gate" in `roost-config`. |
| `e2e` | *Optional.* For the repo that holds the browser e2e suite: `run_all`, `run_tags` (with `{tags}`), `scenarios_dir`, `tag_style`, `backend_marker` (how a UI scenario points at a backend test instead), `secrets_file`, `helpers_hint`. |

## `stack`

The local environment the sessions run and test against.

| Key | Meaning |
|---|---|
| `name` | What it's called, for example "Aspire" or "Docker Compose". |
| `owner_repo` | The repo whose session starts and restarts it. |
| `how` | One sentence on how to run it, given to every session. |
| `never` | *Optional.* Commands not to use instead (for example "yarn dev"). |
| `services` | Each service's `name` and `url`. "The stack answers" means every one returns an HTTP status. |
| `restart_after_api_change` | *Optional.* What to restart after a change a dependent repo needs to see. |
| `extra_resources` | *Optional.* Resources that only start on request, and when they're needed. |
| `test_data` | *Optional.* How to put realistic data into the running stack (a generator, a seed script, a replay), so testing in a browser has something to show. Only ever against the local stack. |
| `flag_state` | *Optional.* A command that prints the running stack's feature-flag state. |
| `flag_tags` | *Optional.* Example e2e tags that gate scenarios by flag state. |
| `telemetry.logs` / `telemetry.traces` / `telemetry.note` | *Optional.* Commands that read the stack's own warnings and traces, with `<service>`. |
| `database.local` | *Optional.* Which database local runs use. |
| `database.apply_migrations` | *Optional.* The command that applies migrations to it. |
| `database.note` | *Optional.* Anything a session would otherwise flag wrongly about it. |

## `vcs`

| Key | Meaning |
|---|---|
| `host` | `github`. |
| `stacking` | `gh-stack`: work goes on stacks of PRs managed with `gh stack` (see the `stacked-prs` skill). (`graphite` and `none` aren't supported yet.) |
| `signed_commits` | `true` if commits must be signed. Never bypass signing. |
| `signing_blocker` | *Optional.* What to tell the user when signing fails, for example "1Password is locked". |
| `signing_errors` | *Optional.* Error text that means signing is blocked on the user. |
| `pr_title` | `conventional` if PR titles must be Conventional Commits. |
| `merge_method` | `squash`, `merge` or `rebase`. |
| `branch_name` | The branch name pattern, with `{key}`. |

## `planning`

| Key | Meaning |
|---|---|
| `lead_repo` | Where the tech lead agent plans. Default the first repo by `order`. |
| `plan_skill` / `execute_skill` | The skills the plan is written and carried out with, for example "superpowers writing-plans". |
| `plans_dir` | Where plans are saved in the lead repo. Default `docs/plans`. |
| `reference_prompt` | *Optional.* A finished tech lead prompt to show how detailed one should be. |
| `services_needing_setup` | *Optional.* Outside services a rollout may need set up (for example "Stripe, WorkOS"). |
| `review_focus` | What `/code-review` should focus on in a slice. |

## `deploy`

| Key | Meaning |
|---|---|
| `migrations_run_on_deploy` | `false` if staging and production don't run migrations on deploy, so every migration needs a deploy note. |
| `migrations_note` | *Optional.* Why, in a few words. |
| `migration_apply` / `migration_verify` | The commands that apply and check migrations in a deployed environment, with `$CONN` read at run time. |
| `secret_read` | How a step reads a secret from the deployed environment. |
| `release_tool` | *Optional.* For example `release-please`. |
| `frontend_host` | *Optional.* For example Vercel. |
| `logs_tool` | *Optional.* Where deployed logs and alerts live. |
| `runbooks.repo` / `dir` / `model` | Where runbooks live, and the one to follow as a model. |
| `runbooks.config_sources` | Where literal deployed values come from. |
| `runbooks.house_rules` | Extra rules for this team's runbooks. |
| `runbooks.never_run_against` | Environments and services no session changes anything in itself: `pair-runbook` never runs a command against them, and other skills hand those steps to the user. |

## `design`

*Optional.* Leave it out if there's no design system; `shape-epic` then asks the user what the prototype should follow.

| Key | Meaning |
|---|---|
| `system` | Its name. |
| `url` | Where it lives. |
| `read_with` | The tools that read it. |
| `read_first` | The files to read before building a prototype. |
| `source_of_truth` | Where the real components live in code. |
| `not_ours` | *Optional.* Other design systems in the same account that must not be used. |

## `qa`

| Key | Meaning |
|---|---|
| `test_account_email` | The pattern for throwaway accounts in exploratory testing. |
| `security_label` | *Optional.* The label for bugs that touch sessions, identity or data between tenants. |

## `roadmap`

*Optional.* Leave it out if epics don't go on a roadmap.

| Key | Meaning |
|---|---|
| `skill` | The skill that puts an epic on the roadmap, for example a team plugin's `add-roadmap-item`. |
| `yes_when` / `no_when` | How to recommend whether an epic goes on it. |

## Machine overrides: `~/.claude/roost/local/<team.name>.yml`

*Optional.* Values that differ on one machine for one team, such as a second development machine with its own database or ports. Same keys as the team config; only the ones that differ. Mappings merge key by key, other values (lists included) replace whole, and `repos` entries match by `name`. Keep it out of the team's repo; it describes one machine.

The file is named after the team (`team.name`), so a machine that works for several teams keeps each team's overrides apart. The older `~/.claude/roost/local.yml` still works when there's no per-team file: it applies when its `team.name` matches the config's, or when it names no team at all, in which case it applies to every team's config on the machine. Give it a `team.name`, or move it to `local/<team.name>.yml`.

```yaml
# ~/.claude/roost/local/Acme.yml
# A second machine with its own Postgres, so it never touches the shared database
stack:
  database:
    local: this machine's own Postgres (Docker container acme-postgres, 172.17.0.1:5432, database acme)
    note: Nothing here uses the shared development database. Migrations and test data stay on this machine.
```
