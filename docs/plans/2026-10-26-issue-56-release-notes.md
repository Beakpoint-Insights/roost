# Release Notes (#56) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `release-notes` skill that drafts paste-ready, customer-facing release notes for one shipped epic, or for everything released since a date: dated by when customers could use each feature, written from what shipped, held when customers can't use it yet, never announced twice, and in the team's voice.

**Architecture:** roost is a Claude Code plugin, so "code" here is skill instructions in Markdown, the config schema and example configs, eval cases, and two small scripts. One new skill (`skills/release-notes/`, with `references/fallback-voice.md`), two new config areas (`repos[].production`, the optional `release_notes` section), hooks in `close-out-epic` step 6 and `setup`, and a "moved to a status since a date" search in each tracker adapter. Behaviour is tested by eval cases (`claude plugin eval`); scripts by their shell tests.

**Tech Stack:** Markdown skills, YAML configs, Python 3 (`scripts/check-references.py`), Bash (`scripts/eval-cases.sh`, the `*.test.sh` scripts), `gh`, `claude plugin eval`, `claude plugin validate --strict`.

**Spec:** `docs/design/issue-56-release-notes.md` (#58), the epic #56, the stories #60 to #63 and their `evals:` comments, and the build guide `docs/design/issue-56-build-guide.html`.

## Global Constraints

- One skill, `skills/release-notes/`, two modes: one epic (offered by `close-out-epic` once production runs the epic), and catch-up since a date.
- A note's date is the first production deploy that included the last change the feature needed, across every repo it touched. Never the tracker's resolution date. Shown in one evidence table: repo, last change, deploy, date.
- `repos[].production` is `{ workflow: <file> }` (that workflow's successful runs), `release` (the published release's date) or `merge` (merging to `main` deploys). A repo without it gets "date not found" with the evidence found, never a guess.
- Written from the slices and their merged PRs, not the epic's plan. Planned but not built: left out, and listed in the checks.
- Held, not dropped: a flag check in the merged diffs or the code around them on `main` (any library, no config key), an unreleased slice, or a correction to past data that hasn't run. Drafted, marked held, says what it waits for, dated `[date]`. Never read a flag provider: say "check the flag's rollout".
- `release_notes.published_url` is optional and fetched. Already covered: dropped or flagged, naming the post. No key, or unreadable: the report says the repeat check wasn't done, and each note gets a "check it isn't already announced" line.
- `release_notes.voice` is one Markdown file, its path relative to the config file, holding every rule including sign-offs and byline. Without it: `skills/release-notes/references/fallback-voice.md`, whose text is the "roost's fallback voice (draft for review)" section of #60, as written. The fallback has no team's brand, sign-offs, byline or product names.
- Catch-up starts from the tracker: epics and tickets moved to `tracker.statuses.done` or `tracker.statuses.ready_for_release` since the date, each dated from its deploys; live before the date: dropped. Epics drafted; standalone stories, tasks and customer-visible bugs listed as candidates, drafted only if picked.
- Unknown facts are `[N]`, listed in the checks. Never guessed.
- One message: every note complete (title, category and date, body, closing line), oldest first, then candidates, then one short checks list. Nothing between notes.
- `examples/release-notes-voice.md` is Acme's made-up voice (sentence-case titles; New, Better, Fixed; at least three rotating sign-offs; the byline "— The Acme team"). `examples/config.example.yml` points `release_notes.voice` at it and has `published_url: https://acme.example/changelog`. `examples/config.github-only.yml` gets `production: release` and no `release_notes`.
- `setup` recommends each repo's `production` and asks for the voice: a path, or an offer to work the rules out from the published notes, shown before anything is saved.
- Out of scope: publishing, reading a flag provider, developer changelogs, translations, screenshots, any one team's voice rules or config.
- Every skill behaves as today for a config with none of the new keys.
- Eval cases are copied word for word from each story's `evals:` comment, committed before the change they test, and pass 3 of 3 runs.

## Review Focus

1. **A busy deploy workflow.** More successful runs since the merge than `gh run list` returns by default (20): the skill must ask for enough (`--limit`, `--created`) and say so if it still can't reach the merge, never report the wrong run or "no deploy". (Task 1.5)
2. **Runs that don't deploy.** A failed or cancelled run, or a run on a PR or another branch, that contains the commit: only a successful run on the default branch or a tag counts, and the date is the first such run whose commit contains the merge commit, by ancestry, not by date. (Task 1.5)
3. **PRs found only by mention.** A slice whose PR doesn't use a closing keyword: find it from the PR side too (key in title, body or branch name); a slice with no PR found is listed in the checks, not treated as "not built". (Task 1.5)
4. **A published page with different titles.** A published post that covers the feature under another name ("Spend Alerts by Email" for "Know right away when spending jumps"): match on what the feature does, not on titles. (Task 2.3; `release-note-already-announced` covers it)
5. **A configured but unreachable `published_url`** (no web tool, a 404, a login wall): "repeat check not done", never "not announced before". (Task 2.3)

---

## Current state

Checked on `main` at `fcb4a34`.

| Question | Finding |
|---|---|
| A tracker search for "moved to a status since a date"? | **None in either adapter.** Jira's Common searches are `skills/roost-config/references/tracker-jira.md:49-53` (children of an epic, not waiting to ship, linked, created during a window, roadmap epics). GitHub's are `tracker-github.md:52-60` (the same five). |
| The exact Jira query | `project = <project> AND status CHANGED TO ("<done>", "<ready_for_release>") AFTER "<date>"` (JQL `CHANGED TO … AFTER`). **Not run**: roost's tracker is GitHub and Acme is made up; see data assumption D5. |
| The exact GitHub query | Done: `gh issue list -R R --state closed --limit 1000 --search "closed:>=<date> reason:completed" --json number,title,closedAt,labels`. Ready for release: `--search 'label:"<ready_for_release>"'`, then each one's timeline for when the label was added: `gh api repos/R/issues/<n>/timeline --paginate --jq '.[] \| select(.event=="labeled" and .label.name=="<ready_for_release>") \| .created_at'`. Checked: `closed:>=2026-10-26` returned 16 issues; #60's timeline returns `labeled story 2026-10-26T20:39:00Z`, so `labeled` events carry `created_at`. |
| How `close-out-epic` step 6 decides production runs the release | `skills/close-out-epic/SKILL.md:68`: "the rollout's deploy step passed, or, for an epic with no rollout, the production deploy that carries its release has run (merging deploys nothing on its own)". It says where to look only for the release workflow (`:70`, `gh run list --workflow <its workflow file>`), not for the production deploy. Nothing reads `production` today. |
| Does any skill date anything from deploy history? | No. `grep -rn production skills/*/SKILL.md` finds only checks that a deploy happened (`close-out-epic:68`), migration notes and runbook rules. |
| How `check-references.py` parses the schema | `schema_keys()` (`scripts/check-references.py:25-54`) reads each `` ## `section` `` heading, then each table row's first cell as keys and every plain lowercase identifier in backticks in the meaning cell as a child key (`:51-53`). Config keys in docs are checked only if they start with a name in `SECTIONS` (`:22`, `:112`). |
| What it needs for `repos[].production` | Nothing new: a `production` row in the `repos` table makes `repos.production` known, and `workflow`, `release`, `merge` in its meaning cell become `repos.production.workflow` / `.release` / `.merge` (the last two are harmless: no doc will write them as keys). `[]` is stripped before lookup (`:61`). |
| What it needs for `release_notes.*` | `release_notes` added to `SECTIONS` (`:22`). **Without it nothing fails:** `release_notes.voic` would be silently unchecked, because the key regex (`:112`) only matches listed sections. The heading regex (`:30`, `\w+`) already accepts `release_notes`. |
| Eval cases that read `examples/config.example.yml` | 19 of 20 prompts name it (`grep -ln config.example.yml evals/*/prompt.md`); the other, `verify-with-eval-cases`, uses `examples/config.github-only.yml`. New keys add facts but change no existing value; none of the 20 cases is about release notes, deploys or voice. |
| Does a change to the examples run the right cases? | `scripts/eval-cases.sh:37` runs **every** case for `examples/config.example.yml`, `skills/roost-config/*` or `.claude-plugin/*`. **No case runs** for `examples/config.github-only.yml` or a new `examples/release-notes-voice.md` (no pattern matches them). So slices 1 to 3 each run all cases in CI, and the GitHub-only example and the voice file are untested by CI selection. |
| Can an eval read a voice file relative to the config? | All 20 cases allow `[Read, Glob, Grep, Skill]`. `examples/release-notes-voice.md` sits beside `examples/config.example.yml`, so `Read` reaches it the same way 19 cases already read the config. The run's working directory is **unknown** (not checked); the existing cases show the config is found. |
| Can an eval fetch `published_url`? | No: no case allows `WebFetch`. So the repeat-check cases give the page's text in the prompt (`release-note-already-announced`), and every other case with `published_url` set must produce "repeat check not done". The skill must accept page text the user pasted as the fetched page. |
| How other skills handle a source they can't read | `skills/shape-epic/references/phase-3-design.md:36` stops ("If you can't reach it, stop and tell the user"); `skills/run-slice/SKILL.md:41-44` marks it ❔ Unknown and names everything unread in one line. The repeat check follows run-slice's way: carry on, say it wasn't done. |
| Baseline checks | `scripts/check-references.py`: "All references resolve (103 files, 21 skills, 185 config keys)". `scripts/check-skills.sh`: pass. `scripts/check-references.test.sh`: "all tests pass". `claude plugin validate --strict .`: "Validation passed". |
| Callers of the scripts | `check-skills.sh`, `check-references.py`, `check-references.test.sh`: `.github/workflows/pr-checks.yml:37,41,43`. `eval-cases.sh`: `.github/workflows/evals.yml:75-89`. |
| Where the hooks go | `setup`: round 3 Repos `skills/setup/SKILL.md:35`, round 6 Planning and deploy `:38`, "4. Check it" `:45`. Schema: `repos` table `config-schema.md:55-72` (`local_stack` `:69`, `apply_gate` `:71`, `e2e` `:72`), `deploy` `:119`. Examples: acme-api `examples/config.example.yml:36`, acme-web `:45`, acme-skills `examples/config.github-only.yml:35`. README: skills table `close-out-epic` row `README.md:182`, release section `:195-201`, "What each skill needs" `:203-225`, Cursor table `:244-252`, happy path close-out `:130`. CONTRIBUTING evals table `:52-73`. |
| Keys in names | `tracker-github.md:8`: a key in a branch is `issue-123`. So the branches are `issue-60-roost` … `issue-63-roost`, and eval tags `issue-60` … `issue-63` as the drafts have. |

### Contradictions with the decisions, in the code or the epic

- `#56`'s Technical Context still lists `release_notes.signoffs`, `release_notes.byline` and "how each repo's production date is found" under `release_notes`. Decisions 1 and 2 (`docs/design/issue-56-release-notes.md`) replaced them with `repos[].production` and one voice file. The plan follows the decisions.
- `#56`'s original description (first comment) has a fallback voice with sign-offs taken from one team's published notes. The approved fallback (#60) has none. The plan uses #60's text; nothing from the original fallback goes into roost.
- `scripts/eval-cases.sh:7` says "A change to … the example config … runs every case", which is true only of `config.example.yml`, not `config.github-only.yml` (`:37`). Task 1.3 fixes the selection.

## Contracts

There are no endpoints. The contracts are config keys and the skill's reply. No repo has a `contract`.

**`repos[].production`** (optional, on each repo), documented in the `repos` table of `config-schema.md`:

| Value | Production date of a change |
|---|---|
| `{ workflow: <file> }` | The first successful run of `.github/workflows/<file>`, on the default branch or a tag, whose head commit contains the change's merge commit |
| `release` | The `publishedAt` of the first published, non-draft GitHub release whose tag contains the merge commit |
| `merge` | The merge to `main` |
| *(missing)* | "date not found", with the evidence found; `[date]` in the note |

**`release_notes`** (optional section), documented as its own `` ## `release_notes` `` section:

| Key | Meaning | Without it |
|---|---|---|
| `voice` | A Markdown file, path relative to the config file, holding every voice rule | `skills/release-notes/references/fallback-voice.md`; the report says so in one line |
| `published_url` | The team's published release notes, fetched for the repeat check | The report says the repeat check wasn't done; each note gets a "check it isn't already announced" line |

**The reply,** in this order and nothing else:

1. Each note, oldest first, nothing between notes: title; category and date line (`[date]` if held or not found); body; closing line; then the voice's sign-off and byline if it has them. A held note says it's held, and what it waits for, on one line directly under the date line.
2. The evidence table: repo, last change, deploy, date (one row per repo per note). It may come before the notes instead.
3. Catch-up only: candidates, one line each.
4. One short checks list: every `[N]` and `[date]`, what was planned but not built, what couldn't be read (deploy history, `published_url`, voice file, a tracker search at its limit), and the fallback voice line.

## Blockers outside the epic

None. The design (#58) and the change that keeps `docs/` out of releases (#64) are merged. #69 (`build-epic` looks for the tech lead prompt only as an attachment) doesn't block the build.

## Rollout

roost ships through release-please: a `feat:` merge opens or updates the release PR, and merging that publishes a new plugin version. No flags, migrations or data. Teams get it when they update the plugin.

Every branch is its own PR against `main` (`vcs.stacking: none`). Each later story starts from the previous story's branch, because consecutive stories edit the same files (`SKILL.md`, the `release_notes` table, `examples/config.example.yml`); it says in its PR that it waits for that PR, and rebases onto `main` once it merges.

| # | Branch | PR title | Deploy | Waits for |
|---|---|---|---|---|
| 0 | `issue-56-release-notes` | `docs: plan for release notes (#56)` | none (docs only, never released, #64/#68) | nothing |
| 1 | `issue-60-roost` | `feat(#60): release notes for one epic, dated by production` | Deploy 1 | the plan's PR |
| 2 | `issue-61-roost` | `feat(#61): hold what customers can't use, skip what's announced` | Deploy 1 | `issue-60-roost` |
| 3 | `issue-62-roost` | `feat(#62): release notes in the team's own voice` | Deploy 2 | `issue-61-roost` |
| 4 | `issue-63-roost` | `feat(#63): catch up on release notes since a date` | Deploy 3 | `issue-62-roost` |

A "Deploy" is merging the release-please PR. **Release #60 and #61 together:** after #60 alone, the skill can't yet tell a flagged or partly released feature from a live one, or a repeat from a new one. #60 says so in its checks (Task 1.5), so it's safe on its own, but a release a team would use for real needs #61. #62 and #63 can each be released alone. Teams' existing configs have none of the new keys: `close-out-epic` and `setup` behave as today without them, and `release-notes` says what it couldn't do.

**Rollout needed: no.** Merging the PRs and the release PRs is the whole rollout: no migration, data change, flag, outside service or ordered deploys across repos.

## Rules that must never break (checklist 5)

roost has no server code. These are the skill's rules, each proven by an eval case:

| Rule | Proven by |
|---|---|
| Never the tracker's resolution date | `release-note-for-one-epic` / `dated-by-deploy`; `release-notes-catch-up` / `right-notes-in-order` |
| Never a guessed date or number | `release-note-date-not-found` / `no-guessed-date`; `release-note-for-one-epic` / `unknown-facts-blank` |
| Never a feature the slices didn't build | `release-note-for-one-epic` / `only-what-shipped` |
| Never a held feature presented as live | `release-note-held-behind-flag` / `held-for-the-flag`; `release-note-held-until-live` / `held-names-both-waits` |
| Never a repeat presented as new | `release-note-already-announced` / `not-announced-twice`; `release-note-without-release-notes-config` / `says-what-it-skipped` |
| Never post or publish anything | `close-out-offers-release-note` / `offers-the-note` (offers, doesn't write); the skill has no step that posts, and allows no tracker write |

## Failure visibility (checklist 6)

The reply is the operator's view. Each of these is a line in the checks list, never silent:

| Failure | Line in the reply | Task |
|---|---|---|
| A repo with no `production` | "Date not found: `<repo>` has no `production` in the config; its last change is `<PR>`, merged `<date>`." | 1.5 |
| Deploy history `gh` can't read, or doesn't reach back to the merge | "Couldn't read `<repo>`'s `<workflow>` runs back to `<date>`: `<error>`." | 1.5 |
| `published_url` missing or unreadable | "Repeat check not done: `<why>`." plus "check it isn't already announced" under each note's checks | 2.3 |
| Voice file unreadable | "Couldn't read the voice file `<path>`; used roost's fallback voice." | 3.3 |
| No voice configured | "Used roost's fallback voice: the config has no `release_notes.voice`." | 1.5 |
| A tracker search at its limit | "The search for `<status>` since `<date>` hit its limit of `<n>`; split it by date." | 4.3 |

## Branch reach (checklist 7)

| Branch | What it changes | Callers outside its subsystem |
|---|---|---|
| `issue-60-roost` | New skill; `close-out-epic` step 6; `repos[].production` in the schema and both example configs; `eval-cases.sh` selection | `close-out-epic` is run by `build-epic` (`skills/build-epic/SKILL.md:80`) and its step-6 Close-out comment is read by `bug-bash:30` and `run-bug:35` to decide "released": the step-6 wording that comment depends on stays. `config.example.yml` is read by 19 eval cases. `eval-cases.sh` is called by `.github/workflows/evals.yml:75-89`. |
| `issue-61-roost` | Skill held/repeat steps; `release_notes` section; `check-references.py` `SECTIONS` | `check-references.py` runs in `pr-checks.yml:41` on every PR: adding a section can only add failures for misspelt `release_notes.*` keys. |
| `issue-62-roost` | Skill voice step; `setup` rounds 3 and 6; `examples/release-notes-voice.md`; `eval-cases.sh` | `setup` is used by every new team; it only gains questions. |
| `issue-63-roost` | Skill catch-up mode; a search added to both tracker adapters | The adapters are read by every skill that touches the tracker; this only adds a row to "Common searches". |

Each branch has one concern (its story) and stays inside the plugin's docs and scripts; none needs splitting.

## Hard parts (checklist 10)

| Component | Shared state | Partial failure | Lifetimes | Real data | Cost of seeing it |
|---|---|---|---|---|---|
| `skills/release-notes/SKILL.md` | n/a: reads only; two runs at once read the same tracker and `gh` data | Read-only, so a stop halfway leaves nothing; a re-run is safe | n/a: no cache | Busy workflows (22 `release-please.yml` runs on 2026-10-26 alone, D2); PRs linked only by mention (16 of 21 merged PRs have no closing reference, D1); releases with `createdAt` ≠ `publishedAt` (D3) | The evidence table grows with repos × notes; fine for a paste |
| `references/fallback-voice.md` | n/a: static text | n/a | n/a | Must contain no team's sign-offs or brand (private-details) | n/a |
| `close-out-epic` step 6 | n/a | Offers only, never writes the note | n/a | Teams without `production` must see step 6 as today | n/a |
| `setup` | n/a | Saves nothing it hasn't shown; a stop before saving leaves the config as it was | n/a | A repo may have several workflows that look like deploys; recommend, don't pick silently | n/a |
| `config-schema.md`, `check-references.py` | n/a | n/a | n/a | n/a: parses one file | Key count rises by about 6 |
| Tracker adapters | n/a | n/a | n/a | GitHub search returns at most 1,000; `gh` defaults to 30 (`tracker-github.md:38`); timelines page | n/a |
| Example configs and voice file | Read by 19+ eval cases at once; read-only | n/a | n/a | A new key could change an unrelated case's reply | Every example change runs all cases (about $3 per full run, `CONTRIBUTING.md:85`) |

**Pre-mortem: "this shipped and caused an incident. What was it?"**

1. **A note went out dated by the wrong deploy,** because the skill matched a run by date, or the run list stopped at 20. *Rule:* a deploy counts only if it succeeded, ran on the default branch or a tag, and its head commit contains the merge commit (`gh api repos/O/R/compare/<merge sha>...<run sha> --jq .status` is `ahead` or `identical`); ask with `--limit 200 --created ">=<merge date>"`, and if the oldest run returned is still after the merge with no match, say the history didn't reach back. *Test:* `release-note-for-one-epic` / `dated-by-deploy`, plus the real-data check in Task 1.8 (roost #52 → `roost-v1.2.0`). Owner: `issue-60-roost`.
2. **A flagged feature was announced as live,** because the flag check sat in the code around the diff, not in it. *Rule:* read the merged diffs and, on `main`, the files and callers that render or route to what they add. *Test:* `release-note-held-behind-flag`. Owner: `issue-61-roost`.
3. **A team's notes repeated an announcement** because `published_url` couldn't be fetched and the skill said nothing. *Rule:* repeat check not done is always said. *Test:* `release-note-without-release-notes-config` / `says-what-it-skipped`. Owner: `issue-61-roost`.
4. **roost shipped one team's voice to every team.** *Rule:* the fallback is #60's text only. *Test:* Task 1.4's grep, and `private-details` on the PR. Owner: `issue-60-roost`.
5. **Upgrading roost broke close-out for teams without `production`.** *Rule:* without `production`, step 6 confirms production as it does today and still offers the note. *Test:* `close-out-sorts-first` still passes (all cases run on `issue-60-roost`), and Task 1.6's review reads step 6 for a config with no `production`. Owner: `issue-60-roost`.
6. **Catch-up missed an epic** because a search returned exactly its limit. *Rule:* a search that returns its limit is split by date, and if it can't be, the checks say so. *Test:* reviewed in Task 4.2 against `tracker-github.md:38`'s rule. Owner: `issue-63-roost`.

## Data assumptions (checklist 11)

| # | Assumption | Query | Result | So |
|---|---|---|---|---|
| D1 | Work built with roost links each merged PR to its ticket | `gh pr list -R Beakpoint-Insights/roost --state merged --limit 100 --json number,closingIssuesReferences,title,body` | 21 merged PRs; 5 have `closingIssuesReferences` (#26, #27, #28, #29, #42); 18 mention some `#N` | **Partly false.** Decision 5 holds (catch-up starts from tickets), but the skill can't rely on closing links: it finds a ticket's PRs by closing reference, by the key in a PR's title, body or branch name (`gh pr list --search "<key> in:title,body"`, `head:issue-<n>`), and from the issue's timeline (`cross-referenced`, `connected`). |
| D2 | `gh run list --workflow <file>` reaches far enough back | `gh run list -R Beakpoint-Insights/roost --workflow release-please.yml --limit 50 --json headSha,createdAt,conclusion` and the same without `--limit` | 22 runs, all on 2026-10-26, 3 `failure`; without `--limit`, 20 | **False at the default.** Pass `--limit` and `--created`; filter `conclusion == success`. Also: `release-please.yml` runs on every push to `main`, so it's not a deploy workflow; roost's own `production` would be `release`. |
| D3 | A GitHub release's date is when users could get it | `gh release list -R Beakpoint-Insights/roost --json tagName,publishedAt,createdAt`; `git merge-base --is-ancestor <#52 merge sha> roost-v1.2.0` and `… roost-v1.1.1` | 4 releases; v1.1.0 `createdAt` 15:00:37Z, `publishedAt` 15:01:29Z. #52's merge `505a1da` is in `roost-v1.2.0`, not in `roost-v1.1.1` | **True, using `publishedAt`** (a draft has none). Matching by ancestry finds v1.2.0, published 2026-10-26T20:06:55Z. For a plugin, "could use" means "could update to". |
| D4 | GitHub can tell when a ticket reached ready-for-release | `gh api repos/Beakpoint-Insights/roost/issues/60/timeline --paginate --jq '.[] \| select(.event=="labeled")'`; `gh issue list … --search 'label:"Ready for Release"'` | `labeled story 2026-10-26T20:39:00Z`; 0 issues carry "Ready for Release" today | True: `labeled` events have `created_at`. Untested on a real "Ready for Release" label because none is in use yet. |
| D5 | Jira's `status CHANGED TO (…) AFTER "<date>"` returns tickets moved since a date, at any depth | For Alan, on a Jira team's site: `project = <project> AND status CHANGED TO ("Done", "Ready for Release") AFTER "2026-09-01" ORDER BY updated ASC` | **Not run** (roost's tracker is GitHub; Acme is made up) | Open question Q1 until the result is in. |

## Checking the plan against itself (checklist 9)

| Contradiction | Resolution |
|---|---|
| Test-first: the eval cases are committed before the skill, but `check-references.py` fails on a grader whose `input_match` names a skill that doesn't exist yet (`scripts/check-references.py:86-89`), so a pushed red commit fails `validate-plugin` | Commit the cases first (red) locally, and don't push until the skill's task is done; the PR is green as a whole. |
| `release-note-fallback-voice` asks for the example config "without its `release_notes` section", which doesn't exist until #61 | Works either way: in #60 there is no section to remove. No change. |
| The fallback says "no sign-off"; `release-notes-catch-up` / `one-message-voice` needs two different sign-offs | That case uses the Acme voice (#62), so it's tagged `issue-63` and can only pass once #62 is merged. #63 starts from #62's branch. |
| #62 AC1 "no fallback rule that conflicts with them" can read as "the fallback fills what the team's file doesn't say"; decision 2 says the file holds every rule and replaces the fallback | Q2. The plan follows decision 2: the file replaces the fallback wholly. |
| #61 adds `published_url` to `config.example.yml`; the #60 cases written before it (`release-note-for-one-epic`, …) then get "repeat check not done" lines | Their graders allow checks after the note (`ready-to-paste`); no change, but #61 runs every case anyway (example config). |
| #63's AC4 "a picked candidate is drafted like an epic's note" needs a second turn, which an eval can't take (build guide, Test coverage) | A manual check on #63's PR, recorded with its evidence (Task 4.4). |

## Open questions

- **Q1 (D5).** Does `status CHANGED TO (…) AFTER` work on the team's Jira, and does it include sub-tasks? Until Alan runs D5, Task 4.2 writes it as the Jira search with a note to check it.
- **Q2.** When a team's voice file is silent on something (say, length), does the fallback fill the gap? Recommendation: no, as decision 2 says; a team copies the fallback as its starting point, so a gap is its choice.
- **Q3.** Should roost's own `.roost/config.example.yml` get `production: release`, so `release-notes` and `close-out-epic` work on roost itself? It isn't a team's private config, but roost's notes aren't customer-facing. Recommendation: yes, in #60, one line; it is how Task 1.8's real-data check runs.
- **Q4.** `scripts/eval-cases.sh` (Task 1.3, 3.2) widens CI's selection a little (the GitHub-only example and the voice file). Fine to add, or keep the script as is?

## How each test is checked

All are eval cases in `evals/`, run with `claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --case <case> --runs 3`, except where the "How" column says otherwise. None is labelled manual.

| Story | Case / check | Grader | How |
|---|---|---|---|
| #60 | `release-note-for-one-epic` | `dated-by-deploy`, `only-what-shipped`, `ready-to-paste`, `unknown-facts-blank`, `uses-release-notes` | Eval |
| #60 | `release-note-fallback-voice` | `plain-words`, `title-and-date-line`, `uses-release-notes` | Eval |
| #60 | `release-note-date-not-found` | `no-guessed-date`, `uses-release-notes` | Eval |
| #60 | `close-out-offers-release-note` | `offers-the-note`, `uses-close-out-epic` | Eval |
| #60 | `repos[].production` keys resolve | — | `scripts/check-references.py` and `scripts/check-references.test.sh` |
| #60 | Fallback has no team's voice | — | Task 1.4's grep; `private-details` in CI |
| #60 | A real date from real history | — | Task 1.8, recorded on the PR |
| #61 | `release-note-held-behind-flag` | `held-for-the-flag`, `uses-release-notes` | Eval |
| #61 | `release-note-held-until-live` | `held-names-both-waits`, `uses-release-notes` | Eval |
| #61 | `release-note-already-announced` | `not-announced-twice`, `uses-release-notes` | Eval |
| #61 | `release_notes` keys in backticks resolve | — | `scripts/check-references.py`, `scripts/check-references.test.sh` |
| #62 | `release-note-team-voice` | `follows-team-voice`, `uses-release-notes` | Eval |
| #62 | `release-note-without-release-notes-config` | `dated-by-release`, `says-what-it-skipped`, `uses-release-notes` | Eval |
| #62 | `setup-asks-production-and-voice` | `asks-and-waits`, `uses-setup` | Eval |
| #63 | `release-notes-catch-up` | `bugs-are-candidates`, `one-message-voice`, `right-notes-in-order`, `uses-release-notes` | Eval |
| #63 | A picked candidate is drafted like an epic's note | — | Manual, once, on the PR (Task 4.4) |
| all | Selection of cases | — | `scripts/eval-cases.test.sh` (Task 1.3) |

Before every push, in every story: `scripts/check-references.py`, `scripts/check-references.test.sh`, `scripts/check-skills.sh`, `claude plugin validate --strict .`, and, once Task 1.3 exists, `scripts/eval-cases.test.sh`.

---

## Story #60: One epic's note, dated by when customers could use it

Branch `issue-60-roost`, from `main`.

### Task 1.1: The eval cases, red

**Files:**
- Create: `evals/release-note-for-one-epic/prompt.md` and `graders/{dated-by-deploy,only-what-shipped,ready-to-paste,unknown-facts-blank,uses-release-notes}.md`
- Create: `evals/release-note-fallback-voice/prompt.md` and `graders/{plain-words,title-and-date-line,uses-release-notes}.md`
- Create: `evals/release-note-date-not-found/prompt.md` and `graders/{no-guessed-date,uses-release-notes}.md`
- Create: `evals/close-out-offers-release-note/prompt.md` and `graders/{offers-the-note,uses-close-out-epic}.md`
- Modify: `CONTRIBUTING.md:73` (four rows after `update-moving`)

- [ ] **Step 1:** Copy each file word for word from #60's `evals:` comment (`gh issue view 60 -R Beakpoint-Insights/roost --comments`). Add the CONTRIBUTING rows, one line each saying what the case checks, in the table's style.
- [ ] **Step 2:** Run `claude plugin eval . --no-publish --trust-plugin --model opus --judge-model sonnet --ablation none --runs 1 --case release-note-for-one-epic` (and the same for the other three). Expected: the three `uses-release-notes` graders fail (no such skill); `offers-the-note` fails (close-out doesn't offer a note).
- [ ] **Step 3:** Commit, don't push: `test(#60): eval cases for one epic's release note`.

### Task 1.2: `repos[].production` in the schema and examples

**Files:**
- Modify: `skills/roost-config/references/config-schema.md:71` (new row after `apply_gate`)
- Modify: `examples/config.example.yml:44` (acme-api), `:64` (acme-web)
- Modify: `examples/config.github-only.yml:44` (acme-skills)
- Modify: `.roost/config.example.yml` (roost repo entry), if Q3 is yes
- Test: `scripts/check-references.test.sh`

**Interfaces:** Produces the key `repos[].production` with values `{ workflow: <file> }`, `release`, `merge`, as in Contracts.

- [ ] **Step 1: Failing test.** In `check-references.test.sh`, add to the planted block `` `repos[].production.workflw` `` and to `want` `"config key that isn't in config-schema.md: repos[].production.workflw"`; also plant a correct `` `repos[].production.workflow` `` and assert it is **not** reported: `! grep -q -F ": repos[].production.workflow" <<<"$out"`.
- [ ] **Step 2:** Run `scripts/check-references.test.sh`. Expected: FAIL (the key isn't documented).
- [ ] **Step 3:** Add the `production` row: *Optional.* How this repo's changes reach production, for dating release notes and confirming a release shipped: `{ workflow: <file> }`, `release`, or `merge`, each as in Contracts. "Without it, `release-notes` says the date wasn't found, and `close-out-epic` confirms production as it would without it." Set `production: { workflow: deploy-production.yml }` on acme-api, `production: merge` on acme-web, `production: release` on acme-skills.
- [ ] **Step 4:** Run `scripts/check-references.test.sh` and `scripts/check-references.py`. Expected: "all tests pass"; "All references resolve".
- [ ] **Step 5:** Commit: `feat(#60): repos[].production says how a repo reaches production`.

### Task 1.3: Run the right cases when an example changes

**Files:**
- Modify: `scripts/eval-cases.sh:7-9,37`
- Create: `scripts/eval-cases.test.sh`
- Modify: `.github/workflows/pr-checks.yml:43` (run the new test after `check-references.test.sh`)

**Interfaces:** Produces the rule "a change to `examples/<file>` other than `config.example.yml` runs the cases whose `prompt.md` names `examples/<file>`". Task 3.2 adds `examples/*.md` → cases tagged `release-notes`.

- [ ] **Step 1: Failing test.** `eval-cases.test.sh` builds a throwaway git repo (as `check-private-details.test.sh` does) with three cases (one naming `examples/config.github-only.yml`, one naming `examples/config.example.yml`, one tagged `close-out-epic`), commits a change to `examples/config.github-only.yml`, and asserts the output is exactly the first case; then a change to `skills/close-out-epic/SKILL.md` gives exactly the third; then `examples/config.example.yml` gives all three.
- [ ] **Step 2:** Run it. Expected: FAIL on the first assertion (empty output).
- [ ] **Step 3:** Add the case to `eval-cases.sh` and fix the comment at `:7-9` to say which example runs what.
- [ ] **Step 4:** Run `scripts/eval-cases.test.sh`. Expected: "eval-cases: all tests pass".
- [ ] **Step 5:** Commit: `ci(#60): run the cases an example file feeds`.

### Task 1.4: The fallback voice

**Files:**
- Create: `skills/release-notes/references/fallback-voice.md`

- [ ] **Step 1: Failing check.** `test -f skills/release-notes/references/fallback-voice.md && ! grep -n -i beakpoint skills/release-notes/references/fallback-voice.md`. Expected: FAIL (no file).
- [ ] **Step 2:** Write the file: a one-paragraph opening saying it's roost's generic voice, used when the config has no `release_notes.voice`, and that a team can copy it as the start of its own; then the "roost's fallback voice (draft for review)" section of #60, word for word, from **Title** to **Word choice**.
- [ ] **Step 3:** Re-run the check, and also compare the sign-offs in #56's first comment against the file by eye: none may appear. Expected: PASS.
- [ ] **Step 4:** Commit with Task 1.5 (the reference has no reader until then).

### Task 1.5: `skills/release-notes/SKILL.md`, one-epic mode

**Files:**
- Create: `skills/release-notes/SKILL.md`

**Interfaces:**
- Consumes: `repos[].production` (Task 1.2), `references/fallback-voice.md` (Task 1.4), the tracker adapter's Read a ticket and Search.
- Produces, as headings later tasks extend: `## 1. Find the work`, `## 2. What shipped`, `## 3. When customers could use it`, `## 4. Can customers use it yet?` (#61), `## 5. Already announced?` (#61), `## 6. The voice` (#62), `## 7. Write the reply`, and `## Catch-up` (#63). The reply as in Contracts.

- [ ] **Step 1:** Front matter modelled on `skills/close-out-epic/SKILL.md:1-4`: `name: release-notes`; a `description` with what it does and triggers ("release notes for PROJ-X", "draft the release note", "what's new since <date>", "catch us up", from `close-out-epic` after release); quote the value if it contains `: `. Then "**First, load the team config with `roost-config`.**" as at `:10`.
- [ ] **Step 2:** The rules, in the sections above, with the values Global Constraints pins. They must say:
  - Evidence the user gives in the conversation counts as read (the evals give everything in the prompt); a source the skill couldn't read is named in the checks.
  - Finding PRs: closing references, the key in a PR's title, body or branch, and the issue's timeline (D1); a slice with no PR found goes in the checks.
  - Planned but not built (Won't Do, or no merged PR): left out of the note, listed in the checks.
  - Dates per `repos[].production`, with the matching rule and `gh` commands from Contracts and pre-mortem 1 (`--limit 200 --created ">=<merge date>"`, `conclusion == success`, event `push` on the default branch or a tag, ancestry by `gh api …/compare`; releases by `publishedAt`, drafts ignored). The feature's date is the latest of its repos'. A repo with no `production`: "date not found", the evidence found, `[date]`, and ask how it reaches production or suggest setting the key.
  - `[N]` for every fact the evidence doesn't give.
  - Until #61: one line in the checks, "Not checked yet: feature flags, unreleased slices and already-published notes." (Task 2.3 replaces it.)
  - Until #62: the voice is always the fallback, and the checks say so in one line.
  - The reply's order and "nothing between notes" from Contracts; never post, publish or change the tracker.
- [ ] **Step 3:** Run `scripts/check-skills.sh`, `scripts/check-references.py`, `claude plugin validate --strict .`. Expected: all pass.
- [ ] **Step 4:** Run the three `release-note-*` cases with `--runs 3`. Expected: every grader passes 3 of 3. On a failure, read the reply in `evals/results/`, fix the skill's wording, re-run.
- [ ] **Step 5:** Commit: `feat(#60): release-notes drafts one epic's note, dated by production`.

### Task 1.6: `close-out-epic` step 6 uses `production` and offers the note

**Files:**
- Modify: `skills/close-out-epic/SKILL.md:68` and a new bullet after `:74`; `:3` (description: "and offers to draft its release note")

- [ ] **Step 1:** At `:68`, say how to confirm the production deploy for each repo with `repos[].production` (the workflow's successful run for the release, the release's publication, or the merge), and "without `production`, confirm it as before and ask the user if it can't be told". Keep "the production deploy that carries its release has run" and the Close-out comment wording that `bug-bash:30` and `run-bug:35` rely on.
- [ ] **Step 2:** New last bullet in step 6: once production runs the epic, offer to draft its release note with the `release-notes` skill. Offer only; don't write it unasked.
- [ ] **Step 3:** Run `close-out-offers-release-note` and `close-out-sorts-first` with `--runs 3`. Expected: all graders pass 3 of 3.
- [ ] **Step 4:** Commit: `feat(#60): close-out-epic offers the release note once production runs it`.

### Task 1.7: README

**Files:**
- Modify: `README.md:130` (append "and after the release ships, offers to draft its release note"), `:201` (new `release-notes` row in "5. Release and operations"), `:218` (`release-notes` needs: tracker access and the `gh` CLI), `:248` (add `release-notes` to the "Work" row)

- [ ] **Step 1:** Make the four edits in each table's style.
- [ ] **Step 2:** Run `scripts/check-references.py`. Expected: pass.
- [ ] **Step 3:** Commit: `docs(#60): release-notes in the README`.

### Task 1.8: Check the story

- [ ] **Step 1:** All four #60 cases, `--runs 3`: pass 3 of 3. Every other case runs in CI (the example config changed); add the `run-evals` label to the PR.
- [ ] **Step 2: Real data, read-only.** In a session with this checkout (`claude --plugin-dir .`) and `.roost/config.yml` carrying `production: release` (Q3), ask "draft the release note for #52's work" with the evidence gathered live. Expected: dated 2026-10-26 from `roost-v1.2.0` (D3), with the evidence table. Paste the reply's table into a PR comment.
- [ ] **Step 3:** Push; open the PR `feat(#60): release notes for one epic, dated by production`, body saying it waits for nothing, and add it to #56's Release order comment.

---

## Story #61: Hold what customers can't use yet, and skip what's announced

Branch `issue-61-roost`, from `issue-60-roost`; rebase onto `main` once #60's PR merges.

### Task 2.1: The eval cases, red

**Files:**
- Create: `evals/release-note-held-behind-flag/`, `evals/release-note-held-until-live/`, `evals/release-note-already-announced/` (prompt and graders word for word from #61's `evals:` comment)
- Modify: `CONTRIBUTING.md` (three rows)

- [ ] **Step 1:** Copy them; add the rows.
- [ ] **Step 2:** Run each with `--runs 1`. Expected: `held-for-the-flag`, `held-names-both-waits` and `not-announced-twice` fail.
- [ ] **Step 3:** Commit, don't push: `test(#61): eval cases for held and already-announced notes`.

### Task 2.2: The `release_notes` section and `published_url`

**Files:**
- Modify: `scripts/check-references.py:22` (add `"release_notes"` to `SECTIONS`)
- Modify: `skills/roost-config/references/config-schema.md` (new `` ## `release_notes` `` section after `deploy`, with `published_url`)
- Modify: `examples/config.example.yml` (new `release_notes:` block with `published_url: https://acme.example/changelog`)
- Test: `scripts/check-references.test.sh`

- [ ] **Step 1: Failing test.** Plant `` `release_notes.publshed_url` `` and expect "config key that isn't in config-schema.md: release_notes.publshed_url".
- [ ] **Step 2:** Run it. Expected: FAIL (the key is silently unchecked today).
- [ ] **Step 3:** Add the section to `SECTIONS`; document the section as *Optional*, with `published_url` as in Contracts; add it to the example.
- [ ] **Step 4:** Run `scripts/check-references.test.sh` and `scripts/check-references.py`. Expected: pass.
- [ ] **Step 5:** Commit: `feat(#61): release_notes.published_url in the config`.

### Task 2.3: Held notes and the repeat check

**Files:**
- Modify: `skills/release-notes/SKILL.md` sections 4 and 5; remove Task 1.5's "Not checked yet" line

- [ ] **Step 1:** Section 4: flags in the merged diffs and, on `main`, the code that renders or routes to what they add (any library; examples of the shapes, not a list of libraries); slices not yet in a production deploy (by the same date rule); corrections to past data not yet run (a job, backfill or script the PRs add that someone runs by hand, with no record of a run). Any of them: drafted, held, one line under the date naming each thing it waits for, `[date]`, and "check the flag's rollout" for a flag. Never claim a rollout was checked.
- [ ] **Step 2:** Section 5: fetch `release_notes.published_url` (WebFetch), or use the page's text if the user gave it. Match on what the feature does, not titles. Covered: drop it, or give it marked as a repeat, naming the post's title and date. Not set or not readable: the checks say "Repeat check not done: <why>", and each note's checks include "check it isn't already announced".
- [ ] **Step 3:** Run the three #61 cases and the four #60 cases, `--runs 3`. Expected: pass 3 of 3.
- [ ] **Step 4:** Commit: `feat(#61): hold what customers can't use yet, skip what's announced`. Push, open the PR (waits for #60's PR), update the Release order comment.

---

## Story #62: The team's own voice

Branch `issue-62-roost`, from `issue-61-roost`; rebase onto `main` once #61's PR merges.

### Task 3.1: The eval cases, red

**Files:**
- Create: `evals/release-note-team-voice/`, `evals/release-note-without-release-notes-config/`, `evals/setup-asks-production-and-voice/` (word for word from #62's `evals:` comment)
- Modify: `CONTRIBUTING.md` (three rows)

- [ ] **Step 1:** Copy; add rows.
- [ ] **Step 2:** Run each with `--runs 1`. Expected: `follows-team-voice` and `asks-and-waits` fail; `says-what-it-skipped` may already pass (that's fine: record it).
- [ ] **Step 3:** Commit, don't push: `test(#62): eval cases for the team's voice and setup`.

### Task 3.2: `release_notes.voice` and Acme's voice

**Files:**
- Modify: `config-schema.md` (`voice` row in `release_notes`)
- Create: `examples/release-notes-voice.md`
- Modify: `examples/config.example.yml` (`voice: release-notes-voice.md`)
- Modify: `scripts/eval-cases.sh`, `scripts/eval-cases.test.sh` (`examples/*.md` → cases tagged `release-notes`)
- Test: `scripts/check-references.test.sh`

- [ ] **Step 1: Failing tests.** Plant `` `release_notes.voic` `` in `check-references.test.sh`; add to `eval-cases.test.sh` a change to `examples/release-notes-voice.md` that must select exactly a case tagged `release-notes`.
- [ ] **Step 2:** Run both. Expected: FAIL.
- [ ] **Step 3:** Document `voice` as in Contracts. Write Acme's voice in the fallback's shape but with: sentence-case titles (only the first word and names capitalised); categories **New**, **Better**, **Fixed**; a sign-off on every note from "Onward!", "Happy shipping!", "Until next time." (rotated, none repeated in a batch); the byline "— The Acme team" at the end of every note. Point the example config at it. Add the `eval-cases.sh` rule.
- [ ] **Step 4:** Run both tests and `scripts/check-references.py`. Expected: pass.
- [ ] **Step 5:** Commit: `feat(#62): release_notes.voice, and Acme's voice as an example`.

### Task 3.3: The skill reads the team's voice

**Files:**
- Modify: `skills/release-notes/SKILL.md` section 6

- [ ] **Step 1:** Resolve `release_notes.voice` relative to the config file's directory; it replaces the fallback wholly (Q2). Unreadable: the fallback, and the checks say so. Not set: the fallback, one line. Replace Task 1.5's "until #62" line.
- [ ] **Step 2:** Run `release-note-team-voice`, `release-note-without-release-notes-config`, and every #60 and #61 case, `--runs 3`. Expected: pass 3 of 3.
- [ ] **Step 3:** Commit: `feat(#62): release notes in the team's own voice`.

### Task 3.4: `setup` asks for `production` and the voice

**Files:**
- Modify: `skills/setup/SKILL.md:35` (round 3), `:38` (round 6), `:45-57` (check it)

- [ ] **Step 1:** Round 3: for each repo, recommend `production` from its workflows (`.github/workflows/*` whose `on:` is a release, tag or production deploy → `{ workflow: <file> }`), its releases (`gh release list` → `release`), or a host that deploys on merge (→ `merge`); say why, and ask.
- [ ] **Step 2:** Round 6: ask for release notes: the published notes' URL, and the voice: a path to the team's file, or an offer to work the rules out from the published notes, starting from `skills/release-notes/references/fallback-voice.md`, shown in full for the user to correct before anything is saved. Optional: a team without customer notes skips it.
- [ ] **Step 3:** Check it: if `release_notes.voice` is set, it exists relative to the config; each `{ workflow: <file> }` exists in its repo (`gh api repos/<github>/contents/.github/workflows/<file>`).
- [ ] **Step 4:** Run `setup-asks-production-and-voice`, `--runs 3`. Expected: pass 3 of 3.
- [ ] **Step 5:** Commit: `feat(#62): setup asks how each repo reaches production, and for the voice`. Push, open the PR (waits for #61's), update the Release order comment.

---

## Story #63: Catch-up since a date

Branch `issue-63-roost`, from `issue-62-roost`; rebase onto `main` once #62's PR merges.

### Task 4.1: The eval case, red

**Files:**
- Create: `evals/release-notes-catch-up/` (word for word from #63's `evals:` comment)
- Modify: `CONTRIBUTING.md` (one row)

- [ ] **Step 1:** Copy; add the row.
- [ ] **Step 2:** Run it, `--runs 1`. Expected: `right-notes-in-order` or `bugs-are-candidates` fails.
- [ ] **Step 3:** Commit, don't push: `test(#63): eval case for catch-up`.

### Task 4.2: "Moved to a status since a date" in both adapters

**Files:**
- Modify: `skills/roost-config/references/tracker-jira.md:53` (new bullet)
- Modify: `skills/roost-config/references/tracker-github.md:60` (new bullet)

- [ ] **Step 1:** Jira: the JQL from Current state, with "check it on your site" until Q1 is answered. GitHub: the two queries from Current state (closed since, and the ready-for-release label's `labeled` event from the timeline), with `--limit 1000` and the split-by-date rule from `tracker-github.md:38`.
- [ ] **Step 2:** Run `scripts/check-references.py`. Expected: pass.
- [ ] **Step 3:** Commit: `feat(#63): tracker searches for tickets moved to a status since a date`.

### Task 4.3: Catch-up mode

**Files:**
- Modify: `skills/release-notes/SKILL.md` (`## Catch-up`; description gains catch-up triggers)

- [ ] **Step 1:** Catch-up: the adapter's new search for `tracker.statuses.done` and `tracker.statuses.ready_for_release` since the date; each epic dated by sections 1 to 5; production date before the cut-off: dropped, with the reason in the checks; standalone stories, tasks and customer-visible bugs as candidates, one line each, not drafted; a picked candidate goes through the one-epic steps; a search at its limit said in the checks. Reply: notes oldest first, candidates, checks.
- [ ] **Step 2:** Run `release-notes-catch-up` and every other `release-notes` case, `--runs 3`. Expected: pass 3 of 3.
- [ ] **Step 3:** Commit: `feat(#63): catch up on release notes since a date`.

### Task 4.4: Manual check, a picked candidate

- [ ] **Step 1:** In a session with this checkout, run the catch-up case's prompt, then answer "include PROJ-2501". Expected: a note for it in the same shape as an epic's (title, category and date February 24, 2026, body, closing line, sign-off and byline), and the checks updated.
- [ ] **Step 2:** Paste both replies in a comment on #63, linked from the PR. Push, open the PR (waits for #62's), update the Release order comment.
