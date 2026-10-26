# Plan the implementation of #56

You are the tech lead agent for this epic, running in the `roost` repo.

**Your job is to plan, not build.** Produce an implementation plan and a set of kickoff prompts for each story. Do not write production code.

---

## 1. Context

**Epic:** #56, "Release notes that match what shipped, in the team's voice". Its tracker is GitHub Issues in `Beakpoint-Insights/roost`. A file attached to an issue is a gist linked from one of its comments.

Read these first:
1. The epic description, and the stories under it.
2. The artifacts listed below.
3. The eval cases for each story: those already in `evals/` tagged with its key, and the drafts in its `evals:` comment, which you commit first, test-first.

| Order | Story | Slice | Tested by |
|---|---|---|---|
| 1 | #60 | One epic's note, dated by when customers could use it | `release-note-for-one-epic`, `release-note-fallback-voice`, `release-note-date-not-found`, `close-out-offers-release-note` |
| 2 | #61 | Hold what customers can't use yet, and skip what's announced | `release-note-held-behind-flag`, `release-note-held-until-live`, `release-note-already-announced` |
| 3 | #62 | The team's own voice | `release-note-team-voice`, `release-note-without-release-notes-config`, `setup-asks-production-and-voice` |
| 4 | #63 | Catch-up since a date | `release-notes-catch-up` |

### Artifacts

Prefer the copies in the repo. The claude.ai links are private to Alan and may not open for you.

| Artifact | Where | What it's for |
|---|---|---|
| **Build guide** | `docs/design/issue-56-build-guide.html` in this repo (from #67); open it in a browser. Live copy: https://claude.ai/artifact/WaV8aPx1DjBS3WKe7347gn | The decisions, the build order, a picture per slice (a mockup, or a map of where things run), and the test coverage table |
| **Design: how a note is built, the config, and the six decisions** | https://github.com/Beakpoint-Insights/roost/pull/58 (merged; `docs/design/issue-56-release-notes.md` on `main`) | The target design: the decisions and what runs where. Its flow diagram is Mermaid, which GitHub renders |

**Decisions already made. Don't reopen them:**
- **Two modes in one skill, `skills/release-notes/`:** one epic (offered by `close-out-epic` once production runs the epic), and catch-up since a date.
- **The date is when customers could use it:** the first production deploy that included the last change the feature needed, across every repo it touched. Never the tracker's resolution date. Shown in one evidence table (repo, last change, deploy, date).
- **`repos[].production` on each repo:** `{ workflow: <file> }` (that workflow's successful runs), `release` (the published release's date) or `merge` (merging to `main` deploys). A repo without it gets "date not found" with the evidence found, never a guess. `close-out-epic` step 6 uses it too.
- **Written from what shipped:** the slices and their merged PRs, not the epic's plan. Anything planned but not built is left out and listed in the checks.
- **Held, not dropped:** a flag check in the merged diffs or the code around them on `main` (any library, no config key), an unreleased slice, or a correction to past data that hasn't run. The note is still drafted, marked held, says what it waits for, and is dated `[date]`. Reading a flag provider's rollout is out of scope: say "check the flag's rollout".
- **Repeat check:** an optional `release_notes` section with `published_url`, fetched; anything already covered is dropped or flagged, naming the post. No key or an unreadable page: the report says the check wasn't done, and each note gets a "check it isn't already announced" line.
- **Voice:** `release_notes.voice` is one Markdown file, its path relative to the config file, holding every rule including sign-offs and byline. Without it, roost's fallback in `skills/release-notes/references/fallback-voice.md`, whose text is the "roost's fallback voice (draft for review)" section of #60, approved as written. The fallback is generic: no team's brand, sign-offs, byline or product names.
- **Catch-up starts from the tracker:** epics and tickets moved to done or ready-for-release since the date, each dated from its deploys; anything live before the date is dropped. Epics are drafted; standalone stories, tasks and customer-visible bugs are listed as candidates, drafted only if picked.
- **Unknown facts are `[N]`,** listed in the checks. Never guessed.
- **One message, ready to paste:** every note complete (title, category and date, body, closing line), oldest first, then candidates, then one short checks list. Nothing between notes.
- **Example files:** Acme's made-up voice in `examples/release-notes-voice.md` (sentence-case titles; New, Better, Fixed; at least three rotating sign-offs; a byline, as #62 gives it), pointed at by `examples/config.example.yml`, which also gets a made-up `published_url: https://acme.example/changelog`. `examples/config.github-only.yml` gets `production: release` and no `release_notes`.
- **`setup`** recommends each repo's `production` and asks for the voice: a path, or an offer to work the rules out from the published notes, shown to the user before anything is saved.
- **Out of scope:** publishing notes, reading a flag provider's rollout, developer changelogs (release-please writes those), translations, screenshots, and any one team's own voice rules or config (they live in that team's config repo, not in roost).

**Starting points in code. Verify each one; don't trust this list:**
- **roost:**
  - `skills/release-notes/` doesn't exist yet. Model its front matter and opening on `skills/close-out-epic/SKILL.md` (lines 1-10: `name`, `description` with trigger phrases, "First, load the team config with `roost-config`").
  - `skills/close-out-epic/SKILL.md:66-70`, "6. After the release ships": confirms production "the rollout's deploy step passed, or … the production deploy that carries its release has run", and already uses `gh run list --workflow <its workflow file>` for release runs. This is where `repos[].production` and the offer to draft the note go.
  - `skills/setup/SKILL.md:35` (round 3, Repos) and `:38` (round 6, Planning and deploy): where `production` per repo and the voice question fit. `:45` "4. Check it".
  - `skills/roost-config/references/config-schema.md:51` (`repos` table, ending with `local_stack` at `:69` and `apply_gate` at `:71`) and `:119` (`deploy`): add `production` to `repos`, and a new `release_notes` section.
  - `scripts/check-references.py:22`, `SECTIONS`: lacks `release_notes`, so `release_notes.*` keys in backticks aren't recognised as config keys until it's added.
  - `examples/config.example.yml:36` (acme-api) and `:45` (acme-web); `examples/config.github-only.yml:35` (acme-skills).
  - `README.md:182` (skills table, `close-out-epic` row), `:218` ("What each skill needs"), `:248` (Cursor table), `:130` (the happy path's close-out step); `CONTRIBUTING.md` evals table, ending at `:67`.
  - `skills/roost-config/references/tracker-jira.md:47-53` and `tracker-github.md` "Common searches": neither has a search for tickets that reached a status since a date.
- **Known gaps to confirm:**
  - No tracker adapter has a "moved to done or ready-for-release since a date" search (Jira: `status changed to … after "<date>"`; GitHub: closed since, plus when a status label was added, from the timeline).
  - No skill reads production deploy history to date anything; `close-out-epic` step 6 only checks a run succeeded.
  - How `scripts/check-references.py` handles a key whose value is a mapping or a word (`production`'s `workflow`, `release`, `merge`).
  - `scripts/eval-cases.sh` runs every case when an example config changes, so slices 1 to 3 each run the whole suite in CI.

---

## 2. Set up the plan's branch

1. From `roost`, create a branch from `main` named `issue-56-release-notes`.
2. Commit the plan (section 3) to it and open a PR against `main`, so the plan is reviewed and merged before the work it describes. Each branch of the work is then its own PR against `main`.

---

## 3. Write the plan

Use the **superpowers writing-plans** skill. Invoke it; don't imitate it.

1. Save the plan to `docs/plans/2026-10-26-issue-56-release-notes.md`. If the repo already keeps plans somewhere else, use that location.
2. Follow the skill's format: small, test-first tasks with exact file paths and commands.
3. Organize the plan by story, in the order above. Within each story, split it by repo, each only if the story needs changes there:
   - **roost:** the plugin's skills and their references, the example configs, its eval cases and its scripts
   - **Order:** repos go in the order above. Say what each later repo waits for, such as an endpoint, a response field or a migration.
4. Plan testing at every level, not only the epic's tests:
   - unit tests for new and changed logic
   - roost: eval cases in evals/ (scripts/eval-cases.sh picks the ones a change affects), and claude plugin validate --strict .
   - `scripts/check-references.py` and `scripts/check-skills.sh` pass locally before every push; `scripts/check-references.test.sh` covers any change to `check-references.py`.
5. For each of the epic's test scenarios (each grader, for eval cases), decide how it's checked: which repo's tests automate it (a backend test, the e2e suite, or another repo's scripted check), or, for a test labelled as manual, that it stays a manual check, run once and recorded, with no automation built for it. For example, "the note is dated March 3, 2026, with an evidence table" belongs in the eval case `release-note-for-one-epic`, and "`release_notes` keys in backticks resolve" belongs in a scripted check, `scripts/check-references.py`. Put that mapping in the plan.
6. Work through the tech lead checklist below. Each item is a general rule followed by what it means for this epic. Give each item its own section in the plan. Where an item doesn't apply, say so in one line.

### Tech lead checklist

1. **Confirm what exists before planning.** Read the code and record what's already there. Don't plan from the ticket text alone. Every finding cites its file and line, or the query you ran and its result. A claim inferred from a name, a date or a comment (a migration's date as the age of the data, a comment as the author's intent) is unchecked until it's checked.
   *In this epic:* Does either tracker adapter have a search for tickets moved to a status since a date, and if not, what's the exact query for each (Jira JQL, and `gh` for GitHub, including when a status label was added)? How does `close-out-epic` step 6 decide production runs the release today? How does `scripts/check-references.py` parse the schema table, and what does it need to accept `repos[].production` and `release_notes.*`? Which existing eval cases name `examples/config.example.yml`, and could the new keys change what they do? Do the evals' `allowed_tools` (`Read, Glob, Grep, Skill`) let the skill read a voice file relative to the config? How do other skills handle a URL they can't fetch? Record each answer, with its file and line, in a "Current state" section.
2. **Write the contracts down.** For every new or changed endpoint, event or schema, give the request, the response and the error shapes, and say which side generates or updates the client.
   *In this epic:* There are no endpoints; the contracts are config keys and the skill's reply. `repos[].production`: `{ workflow: <file> }`, `release` or `merge`. `release_notes.voice`: a Markdown file path, relative to the config file. `release_notes.published_url`: a URL. Each documented in `config-schema.md` with its default and what happens without it. The reply: notes (title, category and date line, body, closing line; `[date]` and `[N]` placeholders), the evidence table, candidates (catch-up), then one checks list. No repo has a `contract`.
3. **Name blockers outside the epic.** List each dependency on another epic, team or service, its current status, and how the plan proceeds: build a stand-in, sequence around it, or mark it blocked.
   *In this epic:* None. The design (#58) and the release-please change that keeps `docs/` out of releases (#64) are both merged.
4. **Plan the rollout.** Say how each branch merges without breaking production: feature flags, migrations, backfills, and what existing customers or data see. Include a **release order** table: every branch in deploy order across every repo, the **deploy** that ships it (Deploy 1, Deploy 2, …), and what each waits for. Each branch is its own PR against `main`; one that needs another's code starts from that branch and is rebased onto `main` once that one merges. End the section with one line, **Rollout needed: yes** or **no**, and why. It's yes when merging and deploying isn't enough on its own: a migration, a backfill or other data change, a feature flag to turn on, setup in another service, or deploys that must happen in a set order.
   *In this epic:* roost ships through release-please: a `feat:` merge opens a release PR, and a release is a new plugin version. No flags, migrations or data. Each slice must leave the skill working on its own, so a release after any slice is safe; say which slices you'd release together. Existing teams' configs have none of the new keys: every skill must behave as today without them, and the new skill must say what it couldn't do.
5. **Enforce the rules on the server.** List every security, billing or data-integrity rule and where the backend enforces it. The UI hiding something doesn't count.
   *In this epic:* doesn't apply as server code, because roost has none. The equivalent is the rules the skill must never break, each proven by an eval case: never the resolution date, never a guessed date or number, never a feature the slices didn't build, never a held feature presented as live, never a repeat presented as new, never posting or publishing anything.
6. **Make failures visible.** Name the failure modes and the log line, metric or alert for each, so an operator can see them.
   *In this epic:* The skill's report is the operator's view. Each of these must be said in the reply, never silent: a repo with no `production` ("date not found"), a deploy history `gh` can't read, `published_url` missing or unreadable ("repeat check not done"), a voice file that can't be read (fallback used), and a tracker search that hit its limit.
7. **Keep branches reviewable, and size them by reach.** Aim for one concern per branch. A goal that sounds small can still reach far, so list every caller of every method whose behavior or signature the branch changes, with its file and line. If the callers span more than one subsystem (an importer, a background job and an API, say), the branch is bigger than its goal: split it into more stacked branches, or say up front which callers it changes and why. If a story's work in one repo is large, split it, and say how.
8. **Record open questions.** Put anything you can't settle from the code or these instructions in an "Open questions" section. Don't guess, and don't silently pick an answer.
9. **Check the plan against itself.** Compare every contract and task with the Global Constraints and the decisions in section 1. List each contradiction (for example a contract that changes a default the constraints say stays the same) and resolve it, or put it in Open questions.
10. **Find the hard parts before building.** For every component the plan changes, answer these in a "Hard parts" table, or write "n/a, because …":
    - **Shared state:** can two callers reach it at the same time? What do they share, and what happens when they overlap?
    - **Partial failure:** if it fails halfway, is cancelled, or runs twice, what's left behind? Is a retry or a re-run safe?
    - **Lifetimes:** what's cached, scoped or disposed, and can anything outlive what it depends on?
    - **Real data:** what values, volumes, duplicates and odd rows does the data it reads hold today?
    - **Cost of seeing it:** does any new metric label, log line or stored row grow with the data?

    Then write a short pre-mortem: "This shipped and caused an incident. What was it?" Each answer that matters becomes a rule in the plan, with the test that proves it, and goes into the kickoff of the branch that owns it.
    *In this epic:* `skills/release-notes/SKILL.md` and `references/fallback-voice.md` (new); `skills/close-out-epic/SKILL.md` step 6; `skills/setup/SKILL.md`; `skills/roost-config/references/config-schema.md`; the two tracker adapters (if a search is added); `scripts/check-references.py`; `examples/config.example.yml`, `examples/config.github-only.yml` and `examples/release-notes-voice.md`, which most existing eval cases read.
11. **Check every assumption about the data.** List each thing the plan assumes about stored data: which values exist, what's unique, ranges, counts, which environment has what. Check each one with a read-only query in the environment that matters (usually production), and record the query and its result. If you can't run it there, write the query for Alan to run, and treat the assumption as an open question until the result is in.
    *In this epic:* Unchecked while shaping: that work built with roost links each merged PR to its ticket (decision 5 rests on it); that `gh run list --workflow <file>` reaches far enough back, and that a run's commit can be matched to the PRs it includes (its default limit is 20 runs); that a GitHub release's date is when users could get it. Check them read-only against this repo, for example `gh release list -R Beakpoint-Insights/roost` and `gh run list -R Beakpoint-Insights/roost --workflow release-please.yml --limit 50 --json headSha,createdAt,conclusion`.
---

## 4. Stop for approval

When the plan is committed, stop. Reply to Alan with:
- the plan's path and the stack name (or, unstacked, the plan's branch and PR)
- a summary of the plan: for each story, the tasks in each repo and their order
- the "Current state" findings, the blockers and the open questions
- anything in the code that contradicts the decisions in section 1, quoted with its file and line
- any contradiction inside the plan itself (checklist item 9)
- the "Hard parts" table and the pre-mortem (checklist item 10)
- each data assumption with its query and result, and any query Alan must run (checklist item 11)
- for each branch, the callers it reaches outside its own subsystem (checklist item 7)
- the **Rollout needed** line from checklist item 4

**Do not post any tracker comments until Alan approves the plan.** If they ask for changes, update the plan, commit it, and stop again.

---

## 5. After approval: post kickoff comments on each story

**First, if the plan says Rollout needed: yes,** set up the deploy work so it can't be missed:
- Find the epic's deploy ticket: a Task under #56 whose title starts with `Deploy #56`. Create it only if there's none, titled `Deploy #56 (Release notes that match what shipped, in the team's voice) to staging and production`. Either way, make sure its Components are set. Never make a second one.
- Use the `write-runbook` skill for the rollout in the plan, on that ticket. It writes the runbook in `docs/runbooks/`, with one sub-task of the deploy ticket for each of its stages. The code doesn't exist yet, so this runbook is a **draft**: say so at its top, get the stages and their sub-tasks right, and write each command as far as the plan allows. The commands are checked against the finished code before release.
- Name the deploy ticket and the runbook in the Release order comment below.

For each of #60, #61, #62 and #63, add one tracker comment per repo that has work in the story. Skip a repo with no work.

**roost:** title it `Kickoff (roost)`; its branch suffix is `roost`.

Each comment is a self-contained prompt for a separate coding agent. Write it so the agent needs nothing else. It must include:

1. **Order:** where this repo comes in the story's order. If it depends on another repo that has work in the story, say: "Do not start until the branch `<name>` in `<that repo>` is pushed with the work you need (stacked: merged into the stack). It provides `<endpoint/field>`."
2. **Branch:** "Create a new branch from `main` for this work, and open its PR against `main`." Give the branch name, `<story key>-<the repo's branch_suffix>`, and, if it needs another branch's code, say "start from `<branch>` instead, say in the PR that it waits for that branch's PR, and rebase onto `main` once that one merges". Add: "Give the PR a Conventional Commit title, for example `feat(<story key>): …`; the title check fails on anything else. Don't write cross-repo dependency notes into the PR; add this branch to the epic's Release order comment instead."
3. **Plan section:** the path to the plan, and which section to execute with the superpowers executing-plans skill.
4. **Scope fence. Copy this word for word:**
   > You are the **[repo name]** agent. Change only **[repo name]**. Do not edit any other repo, even for a "quick" fix. If you find you need a change on the other side, stop, write down exactly what you need, and leave it for the other agent.
5. **E2E tests:** which of the epic's tests (by key or case name) and scenarios to automate at this level of the stack, and which belong to the other layer. If none apply at this level, say "none".
6. **Testing:** "The epic's tests in the tracker are the minimum, not the whole job. Write unit tests for every new or changed function, test-first, plus integration tests where code crosses a boundary (database, third-party service, HTTP). Run the full relevant test suite before you open the PR."
7. **Artifacts:** name the exact artifacts and sections the agent should open. Use the tracker attachment names first and the live links second.
   - **Every comment:** the slice card in the build guide, and the sections of the design doc (its decisions and diagrams) that this branch builds.
8. **Contract:** the endpoints and shapes from the plan that this branch produces or consumes. A comment for a repo with a `contract` must include it word for word:
   None of this epic's repos has a `contract`.
9. **Only ask for what the agent can do.** Don't require steps a coding agent can't do (for example attaching images to a PR). Screenshots go on the story's tracker issue, linked from the PR.
10. **Rules and tests:** in every comment, include the checklist item 10 rules for the components this branch changes, each with a test that proves it. Comments for repos with server code must also include the checklist item 5 server-side rules, each with a test that proves it.
11. **Failure visibility (repos with server code only):** the logs and metrics from checklist item 6 that this branch adds.
12. **Definition of done:** the story's acceptance criteria, and that all tests pass.
13. **Review each task as it's done. Copy this word for word:**
    > After each task in the plan, before starting the next, review that task's changes: run `/code-review` on its commits, or have a fresh-context reviewer read them. Check each finding against the code, fix the real ones test-first, and say which you dismissed and why, citing file and line. Then ask: **what else in the code does the same job?** Search for code with the same interface, base class, naming or pattern. Change it the same way, or record why it stays different. Don't leave the review to the end of the branch: a fix reviewed only at the end can break the next fix.
14. **Evidence in reports:** "Every claim about the code or data in your reports cites its file and line, or the query you ran and its result. Write "unknown" for anything you didn't check; never a guess."

Then post one **Release order** comment on the epic: a table of every branch and PR in deploy order across every repo, with a **Deploy** column, and what each waits for. Keep it current as PRs open.

---

## 6. Report back

When the comments are posted, reply with a table with one row per story: a column per repo saying whether its kickoff comment was posted (yes or no), and the order. If the rollout needed a deploy ticket, also give its key, its sub-tasks and the runbook's path.

Don't change anything in the tracker other than the comments, and the deploy ticket and its sub-tasks, described in section 5.
