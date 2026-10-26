# Contributing to roost

Thanks for helping. Bug reports, fixes, new skills and adapters for more tools are all welcome.

- **Found a bug or want a feature?** [Open an issue](https://github.com/Beakpoint-Insights/roost/issues/new/choose). For support for another tracker, test tool, git host or coding agent, check the [milestones](https://github.com/Beakpoint-Insights/roost/milestones) first; it may already be planned.
- **Have a question or an idea to talk through?** Start a [discussion](https://github.com/Beakpoint-Insights/roost/discussions).
- **Planning a big change?** Open an issue or discussion first, so we can agree on the approach before you write it.
- **Found a security issue?** Don't open an issue. Report it privately, as [SECURITY.md](SECURITY.md) describes.

Everyone who takes part follows the [code of conduct](CODE_OF_CONDUCT.md).

## Adding a skill

Put it in `skills/<name>/SKILL.md`, with any reference files beside it, and add a row to the skill tables in the [README](README.md#skills). Start it by loading the team config with `roost-config`, and use config keys (in backticks, like `tracker.statuses.done`) for anything that differs between teams: names, commands, URLs, statuses. Examples use `PROJ-1234` and the example config's repos.

## Trying changes before they're released

A session runs the installed roost unless it's told otherwise, so a change in your checkout does nothing until it's released and installed. To try it first, start **every** session the work uses (the orchestrator and each repo session) with your checkout:

```
claude --plugin-dir ~/src/roost
```

For that session only, this replaces the installed roost; nothing else changes. To check, ask a session "which roost is running?": it answers with the version, and for a checkout its branch and commit. `run-slice` and `build-epic` ask every session the same question when they start, record the answers, and stop if the sessions don't all run the same roost.

Evals already run against the checkout: `claude plugin eval .` loads the plugin from the folder it's run in.

## Making changes

`main` is protected. Every change goes through a pull request:

1. Branch from `main`, commit (commits must be signed), and open a PR.
2. Give the PR a Conventional Commit title, such as `feat: add the verify-slice skill`. It becomes the commit message when the PR is squash-merged, and release-please reads it.
3. Three checks must pass: `conventional-title` (the PR title), `validate-plugin` and `private-details`. `validate-plugin` runs `claude plugin validate --strict`, which fails on warnings too, and `scripts/check-skills.sh`, which checks that every skill folder has a `SKILL.md` whose `name` matches the folder and that has a description. Run both locally before you push.
   `private-details` fails if the PR's diff, title, body or commit messages add a string from a private list (a repository secret): a team's tracker site, IDs, hostnames and the like. A team's own values belong in its config, never in roost; examples use the made-up Acme team and `PROJ-1234`. The check names the file and line and which list entry matched, never the value. It's skipped on PRs from forks, which don't get the secret, so a maintainer runs it before merging.
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
| `which-roost-is-running` | "Which roost is running?" gets the version from the plugin's own manifest, not a guess |
| `update-moving` | A progress update when nothing needs the user is a `#### 🟢` heading and one plain line |

Run them before merging a change to a skill:

```
claude plugin eval . --no-publish
```

Don't give an eval `SendMessage` or `ListAgents` (with `--allow-tools`). The eval runs on your machine, so a run could message your real repo sessions. A grader can't check a tool the run wasn't given, so write "doesn't message a session" into an `llm` grader's rubric instead of a `tool_used` count.

Each case runs 3 times with roost and 3 times without it, so you can see what the skill changes. A full run costs about $3 on your own Claude account. To check one case quickly: `claude plugin eval . --case <name> --runs 1 --ablation none`. Results go to `evals/results/`, which git ignores.

They also run in CI (`.github/workflows/evals.yml`), on every PR: `scripts/eval-cases.sh` picks the cases the PR's changes can affect. A change to `skills/<name>/` runs the cases tagged `<name>`, a change to a case runs that case, and a change to `roost-config`, the example config or the plugin manifest runs them all. A release PR, or a run started by hand (`gh workflow run Evals`), runs every case: release-please starts that run on its release branch whenever it opens or updates the release PR, since a PR it opens can't start workflows itself. Check that run before merging the release. Every run of a case must pass. The judges that grade the replies get a few verdicts wrong, so a case that fails is run once more, and fails the check only if it fails again. The results are posted on the PR and printed in the run's log, and every run keeps an `eval-results` artifact for 30 days: each case's prompt, reply and grader verdicts, plus the first try of a retried case. Download it with `gh run download <run id> -n eval-results` to read why a case failed. CI needs a Claude credential in a repository secret, `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`) or `ANTHROPIC_API_KEY`; without one, and on PRs from forks, the job skips with a warning.

When you change a skill's behaviour, add or update a case for it, and tag it with the skill's name so CI runs it.

## Versions

Don't edit version numbers by hand. Write commit messages in the Conventional Commits style, and release-please does the rest:

- `feat:` for a new skill or a new capability in one. Bumps the minor version.
- `fix:` for a correction to a skill. Bumps the patch version.
- `docs:` for wording changes in the README or other docs. Bumps the patch version. A change to a skill's instructions changes how the skill behaves, so use `fix:` or `feat:` for those.
- `chore:`, `ci:` and `test:` don't appear in the changelog.
