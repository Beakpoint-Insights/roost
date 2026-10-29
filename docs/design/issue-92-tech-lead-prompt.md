# Plan the implementation of #92

You are the tech lead agent for this epic, running in the `roost` repo.

**Your job is to plan, not build.** Produce an implementation plan and a set of kickoff prompts for each story. Do not write production code.

---

## 1. Context

**Epic:** #92, "retro: carry each run's lessons into the setup". Its tracker is GitHub Issues in `Beakpoint-Insights/roost`. A file attached to an issue is a gist linked from one of its comments.

Read these first:
1. The epic description, and the stories under it.
2. The artifacts listed below.
3. The eval cases for each story: those already in `evals/` tagged with its key, and the drafts in its `evals:` comment, which you commit first, test-first.

| Order | Story | Slice | Tested by |
|---|---|---|---|
| 1 | #111 | Retro on one session | `scripts/retro-moments.test.py` (moment kinds, slow-step grouping, totals, unparseable records, window, redaction); `retro-ranks-and-routes`, `retro-ticket-the-check`; on the PR: a retro on the "Roosting #56" session finds at least 6 of the 8 watch-log problems |
| 2 | #112 | Retro on a run: story, bug or epic | `scripts/retro-moments.test.py` (window from the state file and from comments, sessions from the orchestrator's messages, two sessions in one repo, missing sessions, `run-slice`'s last-turn lookup); on the PR: a retro on #72 finds at least 3 of its 5 lessons |
| 3 | #113 | File roost issues from a retro | `scripts/retro-moments.test.py` (example names, private-details check); `retro-roost-draft-waits` |
| 4 | #114 | Follow-ups between retros | `scripts/retro-moments.test.py` (parsing `retro:` comments, done/open/dropped, first retro, rendering the comment); `retro-recurring-ranks-up` |
| 5 | #115 | Offered after slices, bugs and epics | `scripts/retro-offers.test.py`; on the PR: accepting and declining the offer |

Each story's `evals:` comment holds its script tests (described, for you to write test-first) and its eval cases (in full). The script tests are free and run on every PR; the eval cases are paid and run only before a release or when asked (`CONTRIBUTING.md`, "Evals").

### Artifacts

Prefer the copies in the repo. The claude.ai links are private to Alan and may not open for you.

| Artifact | Where | What it's for |
|---|---|---|
| **Build guide** | `docs/design/issue-92-build-guide.html` on the epic's stack (#110, branch `issue-92-retro-design`); open it in a browser. Live copy: https://claude.ai/artifact/96Z5YcG7iVnLVCU7fsU7eT | The decisions, the build order, a picture per slice (a mockup, or a map of where things run), and the test coverage table |
| **Design: what retro does, its flow, and its nine decisions** | https://github.com/Beakpoint-Insights/roost/pull/110 (`docs/design/issue-92-retro.md`, the bottom PR of the epic's stack) | The target design: the decisions and what runs where. Its flow diagram is Mermaid, which GitHub renders |
| **The #56 watch log** | `~/.claude/roost/state/roost-watch-log.md` on Alan's machine (not in the repo) | Background only: eight problems found by hand while watching #56's run, which slice 1's check on real transcripts should find |
| **#72's run record** | `~/.claude/roost/state/roost/issue-72.md` on Alan's machine (not in the repo) | Background only: the five lessons slice 2's check on real transcripts should find |

**Decisions already made. Don't reopen them:**
- **One skill, `skills/retro/`,** with `references/finding-areas.md` and its script in `skills/retro/scripts/retro_moments.py` (in the skill's folder, so it runs wherever the skill does). Python 3, standard library only. Read-only until the user decides: it never edits a repo, the team config or roost itself, never runs a check itself, and never messages a session.
- **Modes:** one session ("retro on this session", "retro on <session name>") in slice 1; a run ("retro on PROJ-X" for a story, bug or epic, defaulting to the current run) in slice 2. Offered in one line at the end of the reports of `slice-handoff`, `run-bug` and `close-out-epic` in slice 5. No new config section.
- **Finding a run's transcripts (design decision 1):** the window from the state file, or without one from the story's first kickoff comment to its last `run-slice checkpoint:` comment. A repo session's transcript is one in that repo's project folder (`~/.claude/projects/<working directory with / as ->/`), active in the window, that contains a message the orchestrator sent. Not by name, not by `ListAgents` ref (a ref isn't a session id), and not by "newest file". `run-slice`'s last-turn lookup changes to the same lookup.
- **The script reads first (decision 2):** moments of eight kinds (`correction`, `refusal`, `error`, `retry`, `search`, `slow`, `stop`, `blocked`), each with session, time, record id and a trimmed excerpt, plus totals per session. `slow` groups the same command across the run's sessions with each duration, the count and the total. It reads only the fields it needs, and reports records it can't parse instead of failing.
- **Eight finding areas (decision 3):** finding things, automated checks, review rules, agent instructions, tool use, slow steps, access, roost itself, each with where its fix goes. A mechanical rule becomes a lint rule, hook or CI job, never a line in `CLAUDE.md`; a review miss becomes a `review_focus` or coding-standard rule.
- **A finding (decision 4):** area, what happened, evidence, what skipping costs with a concrete case (the shape #99 sets), recommendation, destination; ranked High, Medium, Low. A slow step ranks by its total across the run, High at an hour or more. A finding whose problem has no evidence isn't reported.
- **Checked or Hypothesis (decision 5):** every recommendation is Checked (proven read-only, with the evidence) or a Hypothesis with the check that would settle it, who can run it (a repo session, or only the user) and how long it takes against what the problem costs. At the checkpoint a hypothesis offers: check it now (the user or a repo session runs it, the retro reads the result), ticket the check, not the change (a repo ticket with a `cross-repo-handoff` prompt, or a person-owned task when only the user can run it), or skip.
- **Follow-ups (decision 6):** a comment starting `retro:` on the run's story, bug or epic, with the accepted findings and their links and the rejected ones by title. Each retro opens with the previous one's accepted findings: done, still open, or dropped. A finding that comes back unaddressed ranks one level higher and says how many runs it has recurred on. Matching a new finding to an earlier one is the model's judgment, not an exact match in the script.
- **Redaction (decision 7):** before any quote leaves the script, generic secrets (tokens and keys, connection strings, private keys, `Authorization` headers, email addresses) and every identifying value in the loaded team config and its overrides. A quote that can't be redacted with confidence is dropped and the finding cites its session and time.
- **roost issues (decision 8):** drafted in roost's bug format (`.github/ISSUE_TEMPLATE/bug_report.yml`) or as an epic with a filled-in failure case; the team's names swapped for roost's example names (Acme, `acme-api`, `PROJ-1234`); checked against the same private list, with the same matching as `scripts/check-private-details.sh`; filed with `gh` only once the user approves that exact text. A finding about the team's own setup never goes to roost.
- **Tests:** logic with one right answer goes in the script, tested by `scripts/retro-moments.test.py` and `scripts/retro-offers.test.py` with synthetic fixtures in `scripts/fixtures/retro-moments/`, run on every PR. No real transcript is ever committed. Only the four eval cases need a model. The checks on real transcripts are done on the PR, with the redacted result pasted in.
- **Out of scope:** editing anything the retro reports on; transcripts on another machine or in the cloud; watching a run while it's going; scoring sessions or people; the checks #93 (an epic's parts agree) and #100 (a ledger of shortcuts) do; guided user steps, which #91 will add (until then the retro gives a user-only check's steps inline). Findings about one team's own setup stay in that team's tracker.

**Starting points in code. Verify each one; don't trust this list:**
- **roost:**
  - `skills/retro/` doesn't exist yet. Model its front matter and opening on `skills/close-out-epic/SKILL.md` (lines 1-10: `name`, `description` with trigger phrases, "First, load the team config with `roost-config`").
  - The script's model: `skills/release-notes/scripts/production_date.py` and `catch_up.py` (`argparse`, JSON out), tested by `scripts/production-date.test.py` and `scripts/catch-up.test.py` with fixtures in `scripts/fixtures/production-date/`. CI runs the script tests in `.github/workflows/pr-checks.yml:39-49`; `CONTRIBUTING.md:44` lists them, and `:56` says why logic goes in scripts.
  - `skills/run-slice/SKILL.md:128`: reads a session's last turn as "the newest transcript in `~/.claude/projects/<the repo's project folder>/`". This is what slice 2 changes. Step 0 (`:109-117`) records session names and refs in the state file, and "Keep the state file current" (`:96-107`) says what the state file holds; the retro reads both.
  - The reports that get the offer: `skills/slice-handoff/SKILL.md:102` ("## Report"), `skills/run-bug/SKILL.md:75` ("## Report to the user"), `skills/close-out-epic/SKILL.md:77` ("## Report").
  - `skills/cross-repo-handoff/SKILL.md`: "The prompt's shape" (`:20`) and "Where it goes" (`:41`), for a repo finding's ticket.
  - The tracker adapters' "Common searches": `skills/roost-config/references/tracker-github.md:52` and `tracker-jira.md:47`. Neither has a search for comments starting with a given prefix across the team's tickets.
  - `skills/roost-config/references/config-schema.md:36`: `person_task_label`, for a check only the user can run.
  - `scripts/check-private-details.sh`: the matching decision 8 reuses (case-insensitive fixed strings, an entry reported by number, never its text). It's Bash; the script reimplements its matching in Python rather than calling it (#77 converts Bash to Python).
  - `scripts/check-references.py:5`: paths under `scripts/` and `skills/` in backticks must exist, so a skill that names `skills/retro/scripts/retro_moments.py` must land in the same PR as the script.
  - `scripts/eval-cases.sh:54-55`: a change to `skills/<name>/` selects the cases tagged `<name>`, so slice 5's edits to three skills select those skills' existing cases too when evals run.
  - `README.md:182-184` (skills table) and `:219-222` ("What each skill needs"); `CONTRIBUTING.md` evals table, ending at `:102`.
- **Known gaps to confirm:**
  - How a cross-session message appears in the recipient's transcript. A read of this machine's transcripts while shaping found a `user` record whose text starts "Another Claude session sent a message:" with `<cross-session-message from="…" from-name="roost-ec" …>`. Confirm, and whether `from-name` is stable enough to find the orchestrator's sessions.
  - Which records give a tool call's duration (a `tool_use` and its `tool_result`'s timestamps), and how a permission refusal, a hook's block and a cross-session delivery notice each appear.
  - How to tell the user's own messages from cross-session messages, tool results and system reminders, all of which are `user` records.
  - Whether the orchestrator's own transcript can be found from the sessions it messaged (by `from-name`, or by its kickoff text).
  - No tracker adapter has a search for comments by their first word, which slice 4 needs.

---

## 2. Set up the plan's branch

1. From `roost`, add the plan's branch to the epic's stack, which #110 (the design doc and build guide, branch `issue-92-retro-design`) already starts:
   ```
   gh stack checkout 110
   gh stack add issue-92-retro-plan
   ```
2. Commit the plan (section 3) to that branch, and open its PR against `issue-92-retro-design`, stacked on #110.

---

## 3. Write the plan

Use the **superpowers writing-plans** skill. Invoke it; don't imitate it.

1. Save the plan to `docs/plans/2026-10-28-issue-92-retro.md`. If the repo already keeps plans somewhere else, use that location.
2. Follow the skill's format: small, test-first tasks with exact file paths and commands.
3. Organize the plan by story, in the order above. Within each story, split it by repo, each only if the story needs changes there:
   - **roost:** the plugin's skills and their references, the example configs, its eval cases and its scripts
   - **Order:** repos go in the order above. Say what each later repo waits for, such as an endpoint, a response field or a migration.
4. Plan testing at every level, not only the epic's tests:
   - unit tests for new and changed logic
   - roost: eval cases in evals/ (scripts/eval-cases.sh picks the ones a change affects), and claude plugin validate --strict .
   - `scripts/retro-moments.test.py` and `scripts/retro-offers.test.py`, with synthetic transcripts in `scripts/fixtures/retro-moments/` (including planted secrets and config values), added to `.github/workflows/pr-checks.yml` and `CONTRIBUTING.md`; `scripts/check-references.py` and `scripts/check-skills.sh` pass locally before every push.
5. For each of the epic's test scenarios (each grader, for eval cases), decide how it's checked: which repo's tests automate it (a backend test, the e2e suite, or another repo's scripted check), or, for a test labelled as manual, that it stays a manual check, run once and recorded, with no automation built for it. For example, "the seed is one finding with its count and total" belongs in a scripted check, `scripts/retro-moments.test.py`, and "an unproven speed-up is a Hypothesis that names its check" belongs in the eval case `retro-ranks-and-routes`. Put that mapping in the plan.
6. Work through the tech lead checklist below. Each item is a general rule followed by what it means for this epic. Give each item its own section in the plan. Where an item doesn't apply, say so in one line.

### Tech lead checklist

1. **Confirm what exists before planning.** Read the code and record what's already there. Don't plan from the ticket text alone. Every finding cites its file and line, or the query you ran and its result. A claim inferred from a name, a date or a comment (a migration's date as the age of the data, a comment as the author's intent) is unchecked until it's checked.
   *In this epic:* How does a cross-session message appear in the recipient's transcript, and is `from-name` enough to find a run's sessions? Which records give a tool call's start and end times? How do a permission refusal, a hook's block and a cross-session delivery notice appear? How can the script tell the user's own messages from cross-session messages, tool results and system reminders? Can the orchestrator's transcript be found from the sessions it messaged? What does `run-slice`'s state file hold today (`skills/run-slice/SKILL.md:96-117`), and which fields can the window come from? How do `production_date.py` and its test take `gh` answers from fixtures, and can the retro's tracker reads (comments, ticket states) follow that pattern? Answer from read-only reads of this machine's transcripts in `~/.claude/projects/`, never copying one into the repo. Record each answer, with its file and line, in a "Current state" section.
2. **Write the contracts down.** For every new or changed endpoint, event or schema, give the request, the response and the error shapes, and say which side generates or updates the client.
   *In this epic:* There are no endpoints; the contracts are the script's command line and JSON, and the skill's output. Write down: `retro_moments.py`'s subcommands and arguments (moments for transcripts and a window; finding a run's sessions; redaction against a config; the roost-draft check; parsing `retro:` comments); its JSON (moments, totals, sessions found and not found, unparseable records, redaction drops, check results); its exit codes. Then the checkpoint list's columns, the `retro:` comment's fixed shape, and the roost draft's fields. No repo has a `contract`.
3. **Name blockers outside the epic.** List each dependency on another epic, team or service, its current status, and how the plan proceeds: build a stand-in, sequence around it, or mark it blocked.
   *In this epic:* None blocks the build. #99 (findings say what skipping costs) is open: retro writes its findings in that shape now, without waiting for it. #91 (guided runs) is open: a check only the user can run gets its steps inline. #77 (Bash to Python) is open: reimplement `check-private-details.sh`'s matching in Python rather than calling it. #69 (build-epic can't find a tech lead prompt kept in the repo) is open and affects how this prompt reaches you, not the build.
4. **Plan the rollout.** Say how each branch merges without breaking production: feature flags, migrations, backfills, and what existing customers or data see. Include a **release order** table: every branch in deploy order across every repo, the **deploy** that ships it (Deploy 1, Deploy 2, …), and what each waits for. Branches of one deploy form one stack; a later deploy's branches form their own stack. A repo's stack usually merges and deploys before the stacks of repos that depend on it. End the section with one line, **Rollout needed: yes** or **no**, and why. It's yes when merging and deploying isn't enough on its own: a migration, a backfill or other data change, a feature flag to turn on, setup in another service, or deploys that must happen in a set order.
   *In this epic:* roost ships through release-please: a `feat:` merge opens a release PR, and a release is a new plugin version. `docs/` changes don't release (`release-please-config.json` excludes them), so #110 and the plan's PR ship nothing on their own. No flags, migrations or data. Each slice must leave roost working on its own: say which slices you'd release together, and so which stack (deploy) each branch is on. Teams already using roost get the offer in three reports (slice 5) and nothing else changes for them.
5. **Enforce the rules on the server.** List every security, billing or data-integrity rule and where the backend enforces it. The UI hiding something doesn't count.
   *In this epic:* doesn't apply as server code, because roost has none. The equivalent is the rules the skill must never break, each proven by a script test or an eval case: never a quote with a secret or a team config value in it (enforced in the script, not the prose); never a roost issue filed before the user approves its exact text; never a team-setup finding sent to roost; never an edit, a filed ticket or a message to a session before the user decides; never a check run by the retro itself; never a real transcript committed.
6. **Make failures visible.** Name the failure modes and the log line, metric or alert for each, so an operator can see them.
   *In this epic:* The retro's report is the operator's view. Each must be said in it, never silent: a session that couldn't be found on this machine (named), records the script couldn't parse (counted), quotes dropped because they couldn't be redacted (counted), a draft the private-details check blocked (the entry's number, never its text), a tracker that couldn't be read for follow-ups, and no earlier `retro:` comment ("first retro").
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
    *In this epic:* `skills/retro/scripts/retro_moments.py` (new: reads large transcripts, some still being written by a live session; the redaction; the session lookup); `skills/retro/SKILL.md` and `references/finding-areas.md` (new); `skills/run-slice/SKILL.md:128` (the last-turn lookup); the reports of `skills/slice-handoff/SKILL.md`, `skills/run-bug/SKILL.md` and `skills/close-out-epic/SKILL.md`; `skills/roost-config/references/tracker-github.md` and `tracker-jira.md` (a new search); `.github/workflows/pr-checks.yml` and `CONTRIBUTING.md`.
11. **Check every assumption about the data.** List each thing the plan assumes about stored data: which values exist, what's unique, ranges, counts, which environment has what. Check each one with a read-only query in the environment that matters (usually production), and record the query and its result. If you can't run it there, write the query for Alan to run, and treat the assumption as an open question until the result is in.
    *In this epic:* The data is Claude Code's transcripts, whose format isn't documented. Checked while shaping, on this machine: the roost repo's nine transcripts total 73 MB and one passes 2 MB; records include `user`, `assistant`, `system`, `attachment` and others, with content blocks `text`, `tool_use`, `tool_result` (with `is_error`) and `thinking`; session names are in `customTitle` and `agentName` records; a `ListAgents` ref isn't a session id (ref `0e3260`, transcript `40e81a18….jsonl`); and a cross-session message is a `user` record with `<cross-session-message … from-name="…">`. Unchecked: that the format is the same across Claude Code versions on other machines, that timestamps are on every record the script times, and how large an epic's transcripts get. Check them read-only against `~/.claude/projects/` and record what you ran.
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
- Find the epic's deploy ticket: a Task under #92 whose title starts with `Deploy #92`. Create it only if there's none, titled `Deploy #92 (retro: carry each run's lessons into the setup) to staging and production`. Either way, make sure its Components are set. Never make a second one.
- Use the `write-runbook` skill for the rollout in the plan, on that ticket. It writes the runbook in `docs/runbooks/`, with one sub-task of the deploy ticket for each of its stages. The code doesn't exist yet, so this runbook is a **draft**: say so at its top, get the stages and their sub-tasks right, and write each command as far as the plan allows. The commands are checked against the finished code before release.
- Name the deploy ticket and the runbook in the Release order comment below.

For each of #111, #112, #113, #114 and #115, add one tracker comment per repo that has work in the story. Skip a repo with no work.

**roost:** title it `Kickoff (roost)`; its branch suffix is `roost`.

Each comment is a self-contained prompt for a separate coding agent. Write it so the agent needs nothing else. It must include:

1. **Order:** where this repo comes in the story's order. If it depends on another repo that has work in the story, say: "Do not start until the branch `<name>` in `<that repo>` is pushed with the work you need (stacked: merged into the stack). It provides `<endpoint/field>`."
2. **Branch:** "Create a new branch for this work and add it to the stack for its deploy (see `gh stack --help`)." Name that stack: the epic's stack (bottom branch `issue-92-retro-design`) for the first deploy, and for a later deploy the stack its first branch started (record each deploy's stack in the Release order comment). Give the branch name, `<story key>-<the repo's branch_suffix>`, and the branch it stacks on. If this branch is in the **same deploy** as the branch below it, say "stacked on `<branch>`". If it's the **first branch of a new deploy**, say "start a new stack for Deploy <N>: base it on `<earlier deploy's top branch>` but don't link it into that stack" (see `stacked-prs`, One deploy per stack). Add: "Give the PR a Conventional Commit title, for example `feat(<story key>): …`; the title check fails on anything else. Don't write cross-repo dependency notes into the PR; add this branch to the epic's Release order comment instead."
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
