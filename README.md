# roost

Claude Code skills for taking a product idea to a release, packaged as a plugin: shape an epic, plan it, build it slice by slice through one Claude session per repo, review it as a whole, close it out, QA it, and run the rollout with you one step at a time.

roost is opinionated about **how** the work goes: test-first, small stacked PRs, your decisions at named checkpoints, nothing left only in a chat, and a rollout runbook you run yourself. It's configurable about **where** things live: your tracker and project, your repos, your local stack, your branching and deploy rules. Those come from one team config file.

roost was built at [Beakpoint](https://beakpointinsights.com), which uses it every day.

![A made-up roost session: shaping an epic with recommended answers, approving the plan, progress updates and a YOUR TURN, a slice checkpoint, and the release call](demo/roost.gif)

*A made-up session, sped up. Re-record it with [VHS](https://github.com/charmbracelet/vhs) and [gifsicle](https://www.lcdf.org/gifsicle/): `vhs demo/roost.tape && gifsicle -b -O3 --colors 64 --lossy=30 demo/roost.gif`.*

## Install

```
/plugin marketplace add Beakpoint-Insights/roost
/plugin install roost@roost
```

Skills are then available as `roost:<skill>`, for example `roost:shape-epic`.

## Configure it for your team

Every skill reads one team config before it does anything. Run:

```
/roost:setup
```

It links your team's shared config if you have one, or asks about your tracker, repos, local stack, branching and deploy rules and writes one. [`examples/config.example.yml`](examples/config.example.yml) is a complete example, and [`skills/roost-config/references/config-schema.md`](skills/roost-config/references/config-schema.md) says what every key means.

roost looks for the config in this order: a path you name, `$ROOST_CONFIG`, `.roost/config.yml` in the current repo, then `~/.claude/roost/config.yml`. Most teams keep one config in a private repo, next to any skills of their own, and link it into `~/.claude/roost/config.yml` on each machine so `git pull` keeps everyone in step.

A machine that differs from the rest (its own database, other ports) keeps just those values in `~/.claude/roost/local.yml`, which overrides the shared config on that machine only.

The config never holds secrets: it names where a secret comes from, never its value.

### What's supported

| Area | Config key | Supported now | Not yet |
|---|---|---|---|
| Tracker | `tracker.kind` | Jira (Atlassian MCP) | GitHub Issues, Linear |
| Test management | `tests.kind` | Xray (Cucumber scenarios) | Gherkin files in the repo, none |
| Branching | `vcs.stacking` | `gh stack` on GitHub | Graphite, plain branches |
| Repos | `repos` | Any number, each with its own Claude session, in an order you set | |
| Local stack | `stack` | Anything you run locally (Aspire, Docker Compose, scripts): you give its commands and URLs | |

Each supported tool has an adapter: notes in [`skills/roost-config/references/`](skills/roost-config/references/) that say how to do each operation in that tool. Adding a tracker or test tool means adding an adapter file and a row here.

## From idea to release: the happy path

This is how one epic usually goes through roost. The example team has two repos in its config, a backend and a frontend, so it runs three Claude Code sessions on one machine, each with roost installed:

- the **API session**, opened in the backend repo;
- the **UI session**, opened in the frontend repo;
- the **orchestrator**, a third session opened anywhere. It never edits a repo; it sends the work to the other two and brings their results back to you.

A team with one repo has one worker session; a team with three has three. The made-up epic is PROJ-1234, "New customers can send data minutes after signing up".

### 1. Shape the epic

In any session:

> `/roost:shape-epic` New customers should be able to send data within minutes of signing up.

`shape-epic` works through seven phases: problem, epic, design, slices, tests, build guide and handoff. It asks you about the problem first, and checks with you as each phase finishes. If your config has a roadmap, it asks whether the epic goes on it. At the end, PROJ-1234 has:

- a description with the problem, goals and scope;
- a prototype built from your design system;
- ordered stories, one per slice, each small enough to ship on its own;
- Xray tests with Cucumber scenarios for each story;
- a build guide and a tech lead prompt, attached to the epic.

### 2. Plan the build

In the orchestrator:

> Build PROJ-1234.

`build-epic` starts without asking. The stories have no kickoff comments yet, so it plans first:

1. It sends the epic's tech lead prompt to the lead repo's session, which writes the implementation plan on a new `gh stack`.
2. **You approve the plan,** or ask for changes. The plan ends with **Rollout needed: yes or no**: yes when merging and deploying isn't enough on its own (a migration, a backfill, a feature flag, setup in an outside service).
3. The lead session posts a kickoff comment for each repo on each story, which the build runs from, and a **Release order** comment on the epic. If a rollout is needed, it also creates the epic's deploy ticket and runs `write-runbook`, so each stage of the runbook becomes a sub-task of that ticket, with the same number and name.

### 3. Build the slices

`build-epic` then builds each story in order with `run-slice`:

1. Each repo's session builds its part from its kickoff comment, in the config's order. The stack's owner starts the local stack between them, so a later repo builds against the earlier one's real work.
2. The session with the e2e suite checks the story's tests with `verify-slice-tests`, and every session runs `/code-review` on its stack.
3. **Checkpoint:** you get one list of test results and review findings, each with a recommendation (fix now, ticket for later, or skip), and you decide.
4. The sessions fix the "fix now" items test-first, and the e2e session tests the slice by hand in a real browser. Any bugs it finds come back to you the same way.
5. `slice-handoff` sorts what's left over into the next slice, before release, or later (**you confirm the sorting**), runs every test in the epic so far, and rewrites the next story's kickoff comments to match what was actually built.

Then the next story starts, with no need to ask. Each repo's part of each slice, and each bug fix, is its own PR on the epic's stack, and the Release order comment lists every PR in the order to merge. A migration added along the way goes on the deploy ticket too.

### 4. Get it ready to release

After the last slice, `build-epic` carries on:

1. The "before release" items are fixed (bugs through `run-bug` and `bug-bash`), and every test in the epic runs once more.
2. `review-epic` has every session review the whole epic against `main`, plus a security review of the server code, looking hardest at code no slice review saw. **You decide** each finding.
3. `close-out-epic` gives every open ticket a place: fixed before release, moved to a follow-up epic, or standalone. **You confirm** the places.
4. The e2e session runs `release-qa`: the full e2e run, exploratory testing, and a release call.

### 5. Ship

roost doesn't merge or deploy for you, but it runs the rollout with you. Ask "let's run the PROJ-1234 runbook together" and `pair-runbook` takes you through the deploy ticket's runbook one step at a time: it gives you the command and what to expect, you run it and paste the output, and it checks the result, fills in the run's record and closes the step's sub-task. It stops at each stage's gate for your go-ahead. Merging the stacks is one of the runbook's steps (`stacked-prs` helps with conflicts).

### Where you come in

The skills start work without asking and stop only for your decisions:

- answering `shape-epic`'s questions and approving the tech lead's plan;
- each slice's checkpoint, and each handoff's sorting;
- the `review-epic` findings and the `close-out-epic` places;
- each command of the rollout, which you run yourself, and each stage's gate;
- anything only you can do, such as unlocking commit signing or answering a permission prompt in one of the sessions. Those are listed first, under 🙋 **Your turn**.

At any point, ask the orchestrator "where are we on PROJ-1234?" for a status table. A bug found later, in this epic or anywhere else, goes to "fix PROJ-5678", which runs `run-bug`.

## Skills

The skills are grouped by where they fit in the development cycle, in order.

### 0. Setup

| Skill | What it does |
|---|---|
| `setup` | Links your team's config, or makes one by asking about your tracker, repos, stack, branching and deploy rules, then checks it |
| `roost-config` | Loads the team config and the adapter notes for its tools. Every other skill uses it first; you don't call it yourself |

### 1. Requirements and design

| Skill | What it does |
|---|---|
| `shape-epic` | Shapes an idea into a buildable epic: problem statement, design (a UI prototype, an architecture PR, or both), slices, Xray tests, build guide, and a tech lead prompt attached to the epic |

### 2. Test design

| Skill | What it does |
|---|---|
| `live-verified-bdd` | Writes Cucumber scenarios and checks them against the running app with Playwright before they're finalized |
| `create-xray-test` | Files Cucumber scenarios into new or existing Xray Test issues, with the parent epic, Components and story link. `shape-epic` and `live-verified-bdd` hand off to it |

### 3. Engineering

| Skill | What it does |
|---|---|
| `build-epic` | Builds an epic through the repo sessions: has the lead session plan it from the tech lead prompt (you approve the plan) and post the kickoffs, then runs every slice in order with `slice-handoff` between them, then the before-release work and `release-qa`. Starts and keeps going without asking; stops only for your decisions and real blockers |
| `run-slice` | Drives one slice from kickoff to done through the repo sessions: kickoff prompts, the local stack, test checks, code review, fixes and exploratory testing, stopping for your decisions |
| `slice-handoff` | Closes out a finished slice before the next starts: sorts its carried-over work, runs every test in the epic so far, rewrites the next slice's kickoffs, and checks every stack |
| `run-bug` | Fixes one or more bugs through the repo sessions: triages each, assigns it to you, puts the fix on the epic's stack or on its own PR from `main`, builds each repo's part in order, and checks the test, the test scenario and CI. Starts without asking |
| `review-epic` | Before release, has every session run a whole-epic `/code-review` at high effort against `main` (plus `/security-review` on the server code), marks code that was never reviewed, and brings the findings to one checkpoint |
| `close-out-epic` | Before an epic is released, gives every open ticket a place (fix before release, the epic's follow-up epic, or standalone), moves the deferred ones out with a link back, and after the release checks every ticket ended done |
| `stacked-prs` | Puts branches and PRs on the right `gh stack`, with the "Stacked on" banner, and fixes conflicts on the one branch that has them |
| `cross-repo-handoff` | Writes a prompt another repo's agent can run cold, posted as a comment on the ticket |
| `triage-ticket` | Decides whether a finding in the tracker is accurate and needs fixing, then fixes it test-first if asked |
| `bug-bash` | Fixes a list of bugs in one repo, one branch each, test-first, moving each ticket through the tracker; hands off work that needs another repo |

### 4. Test automation and verification

| Skill | What it does |
|---|---|
| `automate-xray-tests` | Writes the missing automation for a story's Xray tests, then labels and closes the fully passing ones |
| `verify-slice-tests` | After a slice is pushed, proves which Xray tests are automated and passing, closes those, and proposes splits |

### 5. Release and operations

| Skill | What it does |
|---|---|
| `release-qa` | QA for an epic before release: e2e run with every failure sorted, exploratory testing, bugs filed, and a release call |
| `write-runbook` | Writes a recordable, gated runbook with literal commands, kept one to one with the rollout ticket's sub-tasks (one per stage, same number and name) |
| `pair-runbook` | Runs a rollout runbook with you one step at a time: gives the next command, you run it and paste the output, it checks the output, fills in the run's record and updates the step's sub-task. Never runs a rollout command itself |

## What each skill needs

Every skill needs the team config. Install fails quietly if a skill's tools aren't there, so check this first.

| Skill | Needs |
|---|---|
| `shape-epic` | The Atlassian MCP, a Jira API token (`JIRA_EMAIL`, `JIRA_API_TOKEN`) or else Playwright MCP with a signed-in Jira session, Playwright MCP to check the prototype, the tools that read your design system (for Claude Design, its Design tools), and the plan skill your config names (for example the `superpowers` plugin). Publishing the build guide needs claude.ai artifacts, so run it in Claude Code |
| `live-verified-bdd` | Playwright MCP and the app running locally |
| `create-xray-test` | The Atlassian MCP, and `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET`, or else Playwright MCP with a signed-in Jira session |
| `run-slice` | Claude Code, run from a separate orchestrator session, with a session open for each repo on the same machine; the Atlassian MCP; roost in every session |
| `build-epic`, `run-bug`, `review-epic` | Everything `run-slice` needs; `build-epic` also needs what `slice-handoff` and `release-qa` need |
| `slice-handoff` | The Atlassian MCP and a Jira API token (to edit comments; else Playwright MCP with a signed-in Jira session), the `gh` CLI, and the repo sessions open for the epic test run |
| `close-out-epic` | The Atlassian MCP and a Jira API token (to change parents and edit comments; else Playwright MCP with a signed-in Jira session) |
| `stacked-prs` | The `gh` CLI with the `gh stack` extension, and commit signing if your config requires it |
| `cross-repo-handoff` | The Atlassian MCP to post the prompt; works without it by returning the text |
| `triage-ticket` | The Atlassian MCP |
| `bug-bash` | The Atlassian MCP, `gh stack`, and the local stack |
| `automate-xray-tests`, `verify-slice-tests` | The Atlassian MCP, `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` in the environment, and the local stack |
| `release-qa` | The Atlassian MCP, Playwright MCP, and the local stack already running |
| `write-runbook`, `pair-runbook` | A checkout of the repo your runbooks live in, and the Atlassian MCP for the sub-tasks |

## Your own skills

Skills that only make sense for your team (a roadmap in your company's format, a report for your board) belong in a private plugin of your own, next to your config. roost's skills can call them: for example, `shape-epic` asks the skill in `roadmap.skill` to put an epic on the roadmap.

## Using roost in Cursor

Cursor reads skills in the same `SKILL.md` format from `~/.cursor/skills/`. Clone this repo and link the skills there:

```
git clone https://github.com/Beakpoint-Insights/roost.git ~/src/roost
~/src/roost/scripts/link-skills.sh
```

The links point at your clone, so `git pull` in it updates the skills. To use another tool's folder, pass it: `scripts/link-skills.sh ~/.agents/skills`. To undo, run `scripts/link-skills.sh --remove`. Put your config at `~/.claude/roost/config.yml` or set `ROOST_CONFIG`.

The skills were written for Claude Code. In Cursor, set up the same MCP servers (Atlassian and Playwright) so their tool names match, then expect this:

| Skill | In Cursor |
|---|---|
| `setup`, `create-xray-test` | Work |
| `live-verified-bdd` | Works. Its hand-off to `create-xray-test` is by name, so ask for that skill if Cursor doesn't pick it up. |
| `stacked-prs`, `bug-bash`, `cross-repo-handoff`, `triage-ticket`, `write-runbook`, `pair-runbook`, `close-out-epic` | Work |
| `release-qa`, `automate-xray-tests`, `verify-slice-tests` | Work, with the Playwright MCP set up |
| `run-slice`, `build-epic`, `run-bug`, `review-epic` | Don't work. They message other Claude Code sessions, which Cursor can't do. |
| `slice-handoff` | Partly. Sorting, tracker updates and stack checks work; the epic test run needs the repo sessions, so run that step in each repo by hand. |
| `shape-epic` | Partly. The problem statement, slices and tests work. The prototype may need your design system's tools, the build guide is published as a claude.ai artifact, and the tech lead handoff uses your plan skill. Run those phases in Claude Code. |

## Adding a skill

Put it in `skills/<name>/SKILL.md`, with any reference files beside it, and add a row to the tables above. Start it by loading the team config with `roost-config`, and use config keys (in backticks, like `tracker.statuses.done`) for anything that differs between teams: names, commands, URLs, statuses. Examples use `PROJ-1234` and the example config's repos.

## Making changes

`main` is protected. Every change goes through a pull request:

1. Branch from `main`, commit (commits must be signed), and open a PR.
2. Give the PR a Conventional Commit title, such as `feat: add the verify-slice skill`. It becomes the commit message when the PR is squash-merged, and release-please reads it.
3. Two checks must pass: `conventional-title` (the PR title) and `validate-plugin`. `validate-plugin` runs `claude plugin validate --strict`, which fails on warnings too, and `scripts/check-skills.sh`, which checks that every skill folder has a `SKILL.md` whose `name` matches the folder and that has a description. Run both locally before you push.
4. Squash-merge. The branch is deleted automatically.

## Evals

`evals/` holds test cases that check how the skills behave, not just that their files are well-formed. Each case is a prompt plus graders (`evals/<case>/prompt.md` and `evals/<case>/graders/*.md`). Every prompt names [`examples/config.example.yml`](examples/config.example.yml) as its team config, so the cases run the same anywhere. The current cases:

| Case | Checks that |
|---|---|
| `xray-refuses-without-scenarios` | `create-xray-test` stops and points elsewhere when it has no scenarios, instead of writing its own |
| `bdd-for-existing-feature` | Writing scenarios for a feature that already runs goes to `live-verified-bdd`, not straight to filing |
| `shape-epic-starts-with-problem` | A bare idea starts at Phase 1, reads that phase's steps file, and asks questions before building anything |
| `prototype-stops-without-design-system` | The prototype phase stops when it can't reach the config's design system, instead of guessing the look |
| `verify-not-automate` | "Which tests are automated?" after a push goes to `verify-slice-tests`, not `automate-xray-tests` |
| `design-without-ui-is-architecture` | The design phase, for an epic with no UI change, proposes an architecture or design-doc PR and builds no prototype |
| `manual-test-not-automated` | `verify-slice-tests` reports a test labelled manual by its recorded runs, and never proposes automating or splitting it |
| `pasted-stack-steps` | Pasted GitHub stack-conflict steps go to `stacked-prs`, which follows them without asking for a go-ahead |
| `handoff-not-kickoff` | "Slice 3 is done, get ready for the next one" goes to `slice-handoff`, which gathers and sorts first and doesn't start the next slice |
| `epic-starts-without-asking` | "Run the rest of PROJ-X" goes to `build-epic`, which drives the repo sessions instead of building the slices itself, stops only on the real blocker (no sessions to drive), and never asks whether to start |
| `bug-goes-to-the-right-place` | "Fix PROJ-X" goes to `run-bug`, which works out from the bug's parent whether the fix joins an epic's stack or gets its own PR from `main`, and doesn't edit code itself |
| `close-out-sorts-first` | "Close out PROJ-X" goes to `close-out-epic`, which proposes a place for each open ticket and waits, instead of moving anything straight away |
| `epic-review-is-whole-stack` | "Has this epic been reviewed?" goes to `review-epic`, which checks what was and wasn't reviewed and asks for a whole-stack review against `main`, instead of reviewing code itself |
| `runbook-is-paired` | "Let's run the runbook together" goes to `pair-runbook`, which gives one step at a time for you to run, and never runs a rollout command itself |
| `status-is-a-table` | "Where are we on PROJ-X?" gets `run-slice`'s status table, first and on its own, and doesn't offer to start or resume work |
| `question-checked-before-answer` | A question about how the code works, asked mid-slice, gets checked in the code or by the owning session before it's answered, with no guess sent in the meantime |
| `update-your-turn` | A progress update while a session is blocked on the user starts with `## 🙋 YOUR TURN` and the action first |
| `update-moving` | A progress update when nothing needs the user is a `#### 🟢` heading and one plain line |

Run them before merging a change to a skill:

```
claude plugin eval . --no-publish
```

Don't give an eval `SendMessage` or `ListAgents` (with `--allow-tools`). The eval runs on your machine, so a run could message your real repo sessions. A grader can't check a tool the run wasn't given, so write "doesn't message a session" into an `llm` grader's rubric instead of a `tool_used` count.

Each case runs 3 times with roost and 3 times without it, so you can see what the skill changes. A full run costs about $3 on your own Claude account. To check one case quickly: `claude plugin eval . --case <name> --runs 1 --ablation none`. Results go to `evals/results/`, which git ignores.

They also run in CI (`.github/workflows/evals.yml`), on every PR: `scripts/eval-cases.sh` picks the cases the PR's changes can affect. A change to `skills/<name>/` runs the cases tagged `<name>`, a change to a case runs that case, and a change to `roost-config`, the example config or the plugin manifest runs them all. A release PR, or a run started by hand (`gh workflow run Evals`), runs every case. Every run of every case must pass, and the results are posted on the PR. CI needs a Claude credential in a repository secret, `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or `ANTHROPIC_API_KEY`; without one, and on PRs from forks, the job skips with a warning.

When you change a skill's behaviour, add or update a case for it, and tag it with the skill's name so CI runs it.

## Versions

Don't edit version numbers by hand. Write commit messages in the Conventional Commits style, and release-please does the rest:

- `feat:` for a new skill or a new capability in one. Bumps the minor version.
- `fix:` for a correction to a skill. Bumps the patch version.
- `docs:` for wording changes in the README or other docs. Bumps the patch version. A change to a skill's instructions changes how the skill behaves, so use `fix:` or `feat:` for those.
- `chore:`, `ci:` and `test:` don't appear in the changelog.

## License

[MIT](LICENSE)
