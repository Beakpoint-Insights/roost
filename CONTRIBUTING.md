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

## Using roost on roost

roost's own work runs through roost: its issues are the tracker, its eval cases are the tests, and it ships plain PRs. Using it on itself proves it works, and a feature roost needs, built with roost, improves both.

- **Maintainers** shape and build roost's epics with roost (`shape-epic`, then `build-epic`). When roost gets something wrong along the way, open an issue for it.
- **Contributors** are welcome to use roost too, but a normal pull request is fine. Its tracker steps (labels, sub-issues, assigning, statuses) need write access to this repo, which outside contributors don't have. A small fix never needs it; for anything bigger, open an issue first, and a maintainer may shape it into an epic.
- **Either way,** every change gets the same checks, including the evals for the skills it touches.

To use the roost skills here, copy [`.roost/config.example.yml`](.roost/config.example.yml) to `.roost/config.yml` and change anything that differs for you. Your copy is gitignored, and sessions inside the checkout find it before `~/.claude/roost/config.yml`. A session started outside the checkout (an orchestrator) needs `ROOST_CONFIG=<checkout>/.roost/config.yml`.

## Making changes

`main` is protected. Every change goes through a pull request:

1. Branch from `main`, commit (commits must be signed), and open a PR.
2. Give the PR a Conventional Commit title, such as `feat: add the verify-slice skill`. It becomes the commit message when the PR is squash-merged, and release-please reads it.
3. Three checks must pass: `conventional-title` (the PR title), `validate-plugin` and `private-details`. `validate-plugin` runs `claude plugin validate --strict`, which fails on warnings too, and `scripts/check-skills.sh`, which checks that every skill folder has a `SKILL.md` whose `name` matches the folder and that has a description. It also runs `scripts/check-references.py`, which checks, with no model, that everything the skills and docs refer to exists: skills named as skills or in eval graders, reference files and repo paths in backticks, config keys against `config-schema.md`, and relative links. Separately, it runs the scripts' own tests: `scripts/*.test.sh`, `python3 scripts/production-date.test.py`, `python3 scripts/catch-up.test.py` and `python3 scripts/retro-moments.test.py`. Run them all locally before you push.
   `private-details` fails if the PR's diff, title, body or commit messages add a string from a private list (a repository secret): a team's tracker site, IDs, hostnames and the like. A team's own values belong in its config, never in roost; examples use the made-up Acme team and `PROJ-1234`. The check names the file and line and which list entry matched, never the value. It's skipped on PRs from forks, which don't get the secret, so a maintainer runs it before merging.
4. Squash-merge. The branch is deleted automatically.

## Which tests run when

| When | What runs | Costs |
|---|---|---|
| Every push to a PR | `pr-checks`: the PR title, `claude plugin validate --strict`, `scripts/check-skills.sh`, `scripts/check-references.py`, the private-details check, and the scripts' tests | Nothing: no model is called |
| When someone asks: the `run-evals` label, or `gh workflow run Evals` | The eval cases the PR's changes can affect, once each | Real Claude sessions |
| Before a release: the release PR, reopened | The eval cases whose skills changed since the last release | Real Claude sessions |

Why: checks that give the same answer every time and cost nothing run on every change. Evals are slow, cost something, and vary from run to run, like end-to-end tests, so they run when they matter: before a release, and when a change to how a skill behaves needs checking. Logic with one right answer (dates, matching, paging) goes in a script with ordinary tests, which run on every PR, not in a skill's prose, where only an eval could check it. `release-notes`' production date is the first: `skills/release-notes/scripts/production_date.py`, tested by `scripts/production-date.test.py` with recorded `gh` answers in `scripts/fixtures/production-date/`. Scripts are Python 3 with its standard library only; a skill runs one from its own folder (`<skill folder>/scripts/`), which works wherever the skill folder does, Cursor's links included.

**A red eval means "look before release",** not "this PR is broken". The judges get some verdicts wrong, and a model can answer differently from one run to the next. Read the failing case's reply and verdicts (below) and decide: fix the skill, fix the case, or note it for the release.

## Evals

`evals/` holds test cases that check how the skills behave, not just that their files are well-formed. Each case is a prompt plus graders (`evals/<case>/prompt.md` and `evals/<case>/graders/*.md`). Every prompt names [`examples/config.example.yml`](examples/config.example.yml) as its team config, so the cases run the same anywhere. The current cases:

| Case | Checks that |
|---|---|
| `xray-refuses-without-scenarios` | `create-xray-test` stops and points elsewhere when it has no scenarios, instead of writing its own |
| `bdd-for-existing-feature` | Writing scenarios for a feature that already runs goes to `live-verified-bdd`, not straight to filing |
| `shape-epic-starts-with-problem` | A bare idea starts at Phase 1, reads that phase's steps file, and asks questions before building anything |
| `prototype-stops-without-design-system` | The prototype phase stops when it can't reach the config's design system, instead of guessing the look |
| `verify-not-automate` | "Which tests are automated?" after a push goes to `verify-slice-tests`, not `automate-tests` |
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
| `verify-with-eval-cases` | With the GitHub-only example config, `verify-slice-tests` treats a story's tests as eval cases tagged with its key, not Xray tests, and closes nothing |
| `which-roost-is-running` | "Which roost is running?" gets the version from the plugin's own manifest, not a guess |
| `update-moving` | A progress update when nothing needs the user is a `#### 🟢` heading and one plain line |
| `release-note-for-one-epic` | One epic's release note is dated by its production deploy, not the resolution date, with an evidence table; it leaves out a slice that was cut and leaves an unknown number as `[N]`, all in one paste-ready reply |
| `release-note-fallback-voice` | Without the team's own voice, a note follows roost's fallback: a feature title, a category and date line, "Previously… Now…", and no ticket keys, hype or sign-off |
| `release-note-date-not-found` | When a repo's config doesn't say how it reaches production, the note says the date wasn't found and shows the evidence, instead of guessing one |
| `release-note-stacked-slice` | A slice merged into another slice's branch is dated by the commit that brought it onto `main`, not its own merge, and a PR whose key only contains the slice's key is left out |
| `release-note-one-per-feature` | An epic that shipped two separate features gets one note for each, each dated by the last change that feature needed |
| `release-note-held-behind-flag` | A feature that shipped behind a feature flag is drafted but held, waiting on the flag's rollout, with no date yet |
| `release-note-held-until-live` | An epic with a slice not yet deployed and a correction to past data that hasn't run gets a held note naming both waits |
| `release-note-already-announced` | A feature the team's published notes already announce isn't announced again; the draft is dropped or flagged, naming the published post |
| `release-note-announced-as-beta` | A post that announced only a beta of part of a feature doesn't make the finished feature a repeat: it gets a new note about what's new since, naming the post |
| `release-note-team-voice` | With the team's voice file, the note follows it (sentence-case title; New, Better, Fixed; a rotating sign-off; the byline), and no fallback rule is mixed in |
| `release-note-without-release-notes-config` | With no `release_notes` section, the note is dated by its release, uses roost's fallback voice and says so in one line, and says the repeat check wasn't done |
| `release-note-sparse-team-voice` | A team voice that sets only a few rules is still the whole voice: no fallback rule, such as the title word limit, is inherited |
| `release-notes-catch-up` | Catching up since a date drafts each epic customers got since then, oldest first, in one message with rotating sign-offs; leaves out an epic live before the date, saying why; and lists standalone bugs as candidates, not drafts |
| `release-notes-catch-up-filters` | Catching up keeps only tickets still done or ready for release, drops Tests and sub-tasks, and names a ticket that moved back |
| `release-notes-catch-up-lookback` | Catching up includes work marked done before the date that reached production after it, searching back to the newest earlier post, and leaves out what was live before the date |
| `close-out-offers-release-note` | After an epic ships, `close-out-epic` confirms production from each repo's `production` key, then offers to draft the release note instead of writing one unasked |
| `setup-asks-production-and-voice` | `setup` recommends each repo's `production` from its workflows or host, asks for the published notes and the voice, and saves no voice rules the user hasn't seen |
| `retro-ranks-and-routes` | A retro on one session gives one ranked list from the moments script's output, each finding with evidence, what skipping costs, Checked or Hypothesis and a destination; a mechanical mistake becomes a check and a review miss a review rule; nothing changes before the user decides |
| `retro-ticket-the-check` | "Ticket the check" on a hypothesis only the user can check files a person-owned task for the check, not a ticket for the change; an accepted config change is shown for the user to make |

Run them before merging a change to a skill:

```
claude plugin eval . --no-publish --model opus --judge-model sonnet
```

The evals test roost on Opus and judge with Sonnet, in CI too, so pass `--model opus --judge-model sonnet` to compare your results with CI's. Without it, a run uses your account's default model, and on another model some skills don't trigger at all.

Don't give an eval `SendMessage` or `ListAgents` (with `--allow-tools`). The eval runs on your machine, so a run could message your real repo sessions. A grader can't check a tool the run wasn't given, so write "doesn't message a session" into an `llm` grader's rubric instead of a `tool_used` count.

Each case runs 3 times with roost and 3 times without it, so you can see what the skill changes. A full run costs about $3 on your own Claude account. To check one case quickly: `claude plugin eval . --model opus --judge-model sonnet --case <name> --runs 1 --ablation none`. Results go to `evals/results/`, which git ignores.

They also run in CI (`.github/workflows/evals.yml`), but only when someone asks, because every run is a real Claude session paid for by the repository's credential:

- **On a PR, add the `run-evals` label** when it changes how a skill behaves. `scripts/eval-cases.sh` picks the cases the PR's changes can affect: a change to `skills/<name>/` runs the cases tagged `<name>`, a change to a case runs that case, a change to the example voice file `examples/release-notes-voice.md` runs the cases tagged `release-notes`, a change to another file in `examples/` runs the cases whose prompt names it, and a change to `roost-config`, `examples/config.example.yml` or the plugin manifest runs them all. Each runs once, when the label is added; pushes don't run them again. To run them again after more changes, remove the label and add it again. Closing and reopening a PR doesn't run them; only the release PR's reopen does.
- **Before a release,** reopen the release PR (it needs reopening anyway, so its required checks start): the cases whose skills changed since the last release run once each. Check that run before merging the release.
- **By hand,** `gh workflow run Evals` does the same as a release. Name cases with `-f cases="update-moving status-is-a-table"`, or run every case with `-f all=true`, adding `-f runs=3` for three runs each, when you want a full baseline.

Cases run on Opus, judged by Sonnet (the default judge, Haiku, fails too many correct replies on these rubrics), four at a time, through `scripts/run-evals.sh`, which you can run locally too: `scripts/run-evals.sh 1 <case>…`. Every run of a case must pass. The judges that grade the replies get a few verdicts wrong, so a case that fails is run once more, and fails the check only if it fails again. Each attempt has a cost ceiling, so a runaway case stops. The results are posted on the PR and printed in the run's log, and every run keeps an `eval-results` artifact for 30 days: each case's prompt, reply, grader verdicts and output, plus the first try of a retried case. Download it with `gh run download <run id> -n eval-results` to read why a case failed.

CI needs a Claude credential in a repository secret:

- `CLAUDE_CODE_OAUTH_TOKEN` (from `claude setup-token`), preferred. It runs on a subscription, so a heavy day hits a rate limit rather than a bill, and it shares that subscription's limits with your own sessions.
- `ANTHROPIC_API_KEY`, an API key from the Claude Console. It bills the API account per token.

With both set, the workflow uses the token and leaves the key out: Claude Code would otherwise take the key, which ranks above `CLAUDE_CODE_OAUTH_TOKEN` and is always used in `-p` mode when present ("Authentication precedence", [code.claude.com/docs/en/authentication](https://code.claude.com/docs/en/authentication#authentication-precedence)). The run's log says which one it used. Without either, and on PRs from forks, the job skips with a warning.

When you change a skill's behaviour, add or update a case for it, and tag it with the skill's name so CI runs it.

## Versions

Don't edit version numbers by hand. Write commit messages in the Conventional Commits style, and release-please does the rest:

- `feat:` for a new skill or a new capability in one. Bumps the minor version.
- `fix:` for a correction to a skill. Bumps the patch version.
- `docs:` for wording changes in the README or other docs. It never releases on its own: documentation doesn't change the plugin, so it waits for the next `feat:` or `fix:`. A change to a skill's instructions changes how the skill behaves, so use `fix:` or `feat:` for those.
- `docs:`, `chore:`, `ci:` and `test:` don't appear in the changelog.
- A change only to `docs/` (design docs and plans) isn't released, whatever its type: it doesn't change the plugin.
