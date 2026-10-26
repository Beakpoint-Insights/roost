# Tech Lead Prompt Template

Phase 7 fills in this template for one epic. The result is a prompt a tech lead agent can run without any other context.

## How to fill it

- `{{PLACEHOLDER}}` is a value to fill in from the epic. Never leave one in the finished prompt.
- `<!-- FILL: ... -->` explains how to work out a value. Delete the comment once it's filled in.
- **Fixed text** (everything else) stays the same for every epic. Don't reword it. It holds the rules we've learned to want every time.
- Each checklist item has a general rule followed by "*In this epic:*". The rule is fixed. The "In this epic" line comes from this epic's description, its decisions, the code and its Jira links. Gather it from those sources; don't invent it. If an item doesn't apply, write "*In this epic:* doesn't apply, because …".
- Look things up in the code before writing a "Starting points" or "In this epic" line. A line that says what the code does should name a file.
- Write in plain language. No em dashes.
- **Values from the team config** (`roost-config`) are filled in literally, so the prompt stands alone: the tech lead agent doesn't need to read the config. The `CONFIG` rows in the table below say which keys.
- **Only the repos the epic touches.** Values filled "per repo" come from the repos named in the stories' `Repos:` lines (phase 7 step 2), in `repos` order, not from every repo in the config. A repo with no work in the epic isn't named anywhere in the prompt, not even as "no work expected". The lead repo plans either way.
- **Epics with no UI.** Text between `<!-- IF UI -->` and `<!-- END IF UI -->` is fixed text for an epic with a prototype: keep it word for word (and delete the two markers), or, when the epic has no prototype, delete it with its markers. Text between `<!-- IF NO UI -->` and `<!-- END IF NO UI -->` is the reverse. Don't replace the UI text with "None" rows or "this epic has no UI changes".
- **Stacked or not.** Text between `<!-- IF STACKED -->` and `<!-- END IF STACKED -->` is for `vcs.stacking: gh-stack`; text between `<!-- IF NOT STACKED -->` and `<!-- END IF NOT STACKED -->` is for `vcs.stacking: none`, where every branch is its own PR against `main`. Keep the one that applies (deleting its markers) and delete the other.
- **Except values that can differ by machine.** The prompt and the kickoffs it produces live in the tracker, and the epic may be built on a different machine from the one shaping it (one with its own database, in its machine overrides, `~/.claude/roost/local/<team.name>.yml`). So never write `stack.database` values (which database, its address) into the prompt: point at `stack.database.local` in the roost config instead, which every session loads for its own machine. Commands that are the same everywhere (`stack.how`, `stack.never`) are still filled in literally.

The sources for each value:

| Value | Source |
|---|---|
| Stories, order, tests | Jira children of the epic and their "is tested by" links (from phases 4 and 5) |
| Decisions | Settled during shaping: the epic description, the user's answers in this session, story descriptions |
| Artifacts | The build guide (phase 6), the prototype and the design-doc PR (phase 3), the design system, and any cross-epic guide the user mentioned |
| Prototype screens per story | The prototype's controls bar, and the "UI" section of each story. Only with a prototype |
| Starting points, known gaps | A read of each repo the epic touches |
| Blockers | Dependencies in the epic and story descriptions, plus Jira status of what they point to |
| Hard-parts components, data assumptions | The components the epic changes (a read of the code), and the data facts its decisions rest on (queries and results in the epic's comments and this session) |
| `{{REVIEWER}}` | The person running `shape-epic`: their first name, from "Who am I" in the tracker adapter. They approve the plan. |
| `{{LEAD_REPO}}` | CONFIG `planning.lead_repo` |
| `{{OTHER_REPOS}}` | CONFIG every other repo the epic touches, by `name`, as sibling folders (`../<name>`). If there are none, delete the sentence that names them. |
| `{{TRACKER_SITE}}`, `{{TRACKER_ID}}` | CONFIG `tracker.jira.site` and `tracker.jira.cloud_id` |
| `{{PLAN_SKILL}}`, `{{EXECUTE_SKILL}}`, `{{PLANS_DIR}}` | CONFIG `planning.plan_skill`, `planning.execute_skill`, `planning.plans_dir` |
| `{{REPO_SPLIT}}`, `{{REPO_TESTS}}` | CONFIG one bullet per repo the epic touches, in `repos` order, from its `name`, `owns` and `tests` |
| `{{DESIGN_ROW}}` | CONFIG `design`: its name, `url` and `source_of_truth`. With no `design`, or no UI in the epic, delete the row |
| `{{SERVICES_NEEDING_SETUP}}` | CONFIG `planning.services_needing_setup`, or "another service" |
| `{{KICKOFF_TITLES}}`, `{{CONTRACTS}}` | CONFIG each touched repo's `kickoff_title` and `branch_suffix` (its `role` when there's none), and the `contract` of each touched repo that has one |
| `{{FLAG_STATE}}` | CONFIG `stack.flag_state` and `stack.flag_tags`. With neither, delete the sentence |
| `{{LOCAL_STACK}}` | CONFIG `stack.how`, `stack.never`, `stack.extra_resources`, `stack.database.apply_migrations`, and whether `deploy.migrations_run_on_deploy` is false. Not the database itself: see "Except values that can differ by machine" |
| `{{APPLY_GATE_ITEM}}` | CONFIG each touched repo's `apply_gate` (`plan`, `apply`, `who`, `when`) |
| `{{PR_TITLE_RULE}}` | CONFIG `vcs.pr_title`: for `conventional`, "Give the PR a Conventional Commit title, for example `feat(<story key>): …`; the title check fails on anything else." |

---

## Template

```markdown
# Plan the implementation of {{EPIC_KEY}}

You are the tech lead agent for this epic, running in the `{{LEAD_REPO}}` repo. The other repos this epic touches are the siblings {{OTHER_REPOS}}. Read them freely, but do not change them during this task.

**Your job is to plan, not build.** Produce an implementation plan and a set of kickoff prompts for each story. Do not write production code.

---

## 1. Context

**Epic:** {{EPIC_KEY}}, "{{EPIC_TITLE}}". Jira site `{{TRACKER_SITE}}`, cloud ID `{{TRACKER_ID}}`.

Read these first:
1. The epic description, and the stories under it.
2. The artifacts listed below. Download the Jira attachments and open them.
3. The Xray tests linked to each story. Their Cucumber scenarios are in the Xray "Test details" panel. If you can't read that panel, use the test summaries in the build guide.

| Order | Story | Slice | Tested by |
|---|---|---|---|
{{STORY_ROWS}}
<!-- FILL: one row per story, in build order: "| 1 | PROJ-XXXX | Title | PROJ-YYYY, PROJ-ZZZZ |". -->

{{CROSS_EPIC_TESTS_NOTE}}
<!-- FILL: name any test under the epic that spans other epics, and say "Don't plan it here." Delete this line if there are none. -->

### Artifacts

Prefer the Jira attachments. The claude.ai links are private to {{REVIEWER}} and may not open for you.

| Artifact | Where | What it's for |
|---|---|---|
| **Build guide** | Jira attachment on {{EPIC_KEY}}: `{{EPIC_KEY}} Build Guide.html`. Live copy: {{BUILD_GUIDE_URL}} | The decisions, the build order, a picture per slice (a mockup, or a map of where things run), and the test coverage table |
<!-- IF UI -->
| **Prototype** | Jira attachment on {{EPIC_KEY}}: `{{EPIC_KEY}} Prototype.html` | The clickable target UI in light and dark mode. Use the controls bar at the top to switch screens and states (see the next table) |
{{DESIGN_ROW}}
<!-- FILL: "| **<design.system>** | <design.url>, which mirrors `<design.source_of_truth>` | Tokens, components and page patterns. The code is the source of truth |". Delete this line if the config has no design system. -->
<!-- END IF UI -->
{{DESIGN_DOC_ROW}}
<!-- FILL: the phase 3 design-doc PR, as "| **Design: <what it holds, for example the ADRs and deployment views>** | <PR link> | The target design: the decisions and what runs where. How to view its diagrams, if they need a tool |". Delete this line if the epic has no design doc. -->
{{EXTRA_ARTIFACT_ROWS}}
<!-- FILL: any other artifact used during shaping, such as a cross-epic guide or another epic's design doc, as "| **Name** | link | Background only |". Delete this line if there are none. -->

<!-- IF UI -->
Prototype screens for each story:

| Story | Prototype screen and states |
|---|---|
{{PROTOTYPE_SCREEN_ROWS}}
<!-- FILL: one row per story that changes the UI. Use the exact screen and state names from the prototype's controls bar. -->

{{OUT_OF_SCOPE_SCREENS_NOTE}}
<!-- FILL: name any prototype screens that belong to other epics, and say "Ignore them." Delete this line if there are none. -->
<!-- END IF UI -->

**Decisions already made. Don't reopen them:**
{{DECISIONS}}
<!-- FILL: one bullet per decision settled during shaping, each starting with a bold label. Include: product and behavior decisions, what to keep or remove in existing code (by class or method name), exact values customers see (URLs, header names, variable names), UI rules (when the epic has a prototype and the config has a design system, always: "every UI change follows <design.system>, which mirrors `<design.source_of_truth>`. The prototype shows the target UI. Copy its structure, wording and states, but build the screens from the real components, not from the prototype's CSS."), and an "Out of scope" bullet naming related epics, stories and bugs. -->

**Starting points in code. Verify each one; don't trust this list:**
{{STARTING_POINTS}}
<!-- FILL: one bullet per repo the epic touches, each with the files and classes this epic will touch, found by reading those repos. Then a "Known gaps to confirm" bullet listing what the code doesn't do yet or what you couldn't tell. -->

---

## 2. Set up the plan's branch

<!-- IF STACKED -->
1. From `{{LEAD_REPO}}`, create a new stack named after the epic:
   ```
   gh stack init {{STACK_NAME}}
   ```
2. Commit the plan (section 3) to the base branch of that stack.
<!-- END IF STACKED -->
<!-- IF NOT STACKED -->
1. From `{{LEAD_REPO}}`, create a branch from `main` named `{{STACK_NAME}}`.
2. Commit the plan (section 3) to it and open a PR against `main`, so the plan is reviewed and merged before the work it describes. Each branch of the work is then its own PR against `main`.
<!-- END IF NOT STACKED -->
<!-- FILL: STACK_NAME is the epic key plus a short kebab-case version of the title, for example PROJ-2306-be-ready-to-send-spans. -->

---

## 3. Write the plan

Use the **{{PLAN_SKILL}}** skill. Invoke it; don't imitate it.

1. Save the plan to `{{PLANS_DIR}}/{{DATE}}-{{STACK_NAME_LOWER}}.md`. If the repo already keeps plans somewhere else, use that location.
2. Follow the skill's format: small, test-first tasks with exact file paths and commands.
3. Organize the plan by story, in the order above. Within each story, split it by repo, each only if the story needs changes there:
   {{REPO_SPLIT}}
   <!-- FILL: one bullet per repo the epic touches, in order, as "**<name>:** <owns>". -->
   - **Order:** repos go in the order above. Say what each later repo waits for, such as an endpoint, a response field or a migration.
4. Plan testing at every level, not only the Jira e2e tests:
   - unit tests for new and changed logic
   {{REPO_TESTS}}
   <!-- FILL: one bullet per repo the epic touches, from its `tests`. -->
   {{EXTRA_TEST_TOOLING}}
   <!-- FILL: any special test tooling this epic needs, such as "the payment provider's test clocks wherever billing behavior over time matters". Delete this line if there is none. -->
5. For each Xray scenario, decide how it's checked: which repo's tests automate it (a backend test, the e2e suite, or another repo's scripted check), or, for a test labelled as manual, that it stays a manual check, run once and recorded, with no automation built for it. {{LAYER_EXAMPLE}} Put that mapping in the plan.
   <!-- FILL: LAYER_EXAMPLE is one scenario from this epic's tests for each way this epic's tests are checked, as "For example, "…" belongs in <the backend, the UI, a scripted check in <repo>>, and "…" stays a manual check." Name only the ways this epic uses. -->
6. Work through the tech lead checklist below. Each item is a general rule followed by what it means for this epic. Give each item its own section in the plan. Where an item doesn't apply, say so in one line.

### Tech lead checklist

1. **Confirm what exists before planning.** Read the code and record what's already there. Don't plan from the ticket text alone. Every finding cites its file and line, or the query you ran and its result. A claim inferred from a name, a date or a comment (a migration's date as the age of the data, a comment as the author's intent) is unchecked until it's checked.
   *In this epic:* {{CL_CURRENT_STATE}}
   <!-- FILL: the specific questions to answer from the code (the "Known gaps to confirm", phrased as questions). End with: "Record each answer, with its file and line, in a "Current state" section." -->
2. **Write the contracts down.** For every new or changed endpoint, event or schema, give the request, the response and the error shapes, and say which side generates or updates the client.
   *In this epic:* {{CL_CONTRACTS}}
   <!-- FILL: name each new or changed endpoint, list field and response shape. Always add, for each repo the epic touches that has a `contract`: "<repo name>: <contract>. The agent for <the repo it depends on> (or `run-slice`) makes sure the local stack runs the right branch." -->
3. **Name blockers outside the epic.** List each dependency on another epic, team or service, its current status, and how the plan proceeds: build a stand-in, sequence around it, or mark it blocked.
   *In this epic:* {{CL_BLOCKERS}}
   <!-- FILL: each dependency with its Jira key and current status, checked in Jira now, and the choice the tech lead must make. -->
4. **Plan the rollout.** Say how each branch merges without breaking production: feature flags, migrations, backfills, and what existing customers or data see. Include a **release order** table: every branch in deploy order across every repo, the **deploy** that ships it (Deploy 1, Deploy 2, …), and what each waits for. <!-- IF STACKED -->Branches of one deploy form one stack; a later deploy's branches form their own stack. A repo's stack usually merges and deploys before the stacks of repos that depend on it.<!-- END IF STACKED --><!-- IF NOT STACKED -->Each branch is its own PR against `main`; one that needs another's code waits for it to merge, then starts from the new `main`.<!-- END IF NOT STACKED --> End the section with one line, **Rollout needed: yes** or **no**, and why. It's yes when merging and deploying isn't enough on its own: a migration, a backfill or other data change, a feature flag to turn on, setup in {{SERVICES_NEEDING_SETUP}}, or deploys that must happen in a set order.
   *In this epic:* {{CL_ROLLOUT}}
   <!-- FILL: the feature flags involved (search each repo the epic touches), any backfill, and any existing customer or data that must not change. -->
5. **Enforce the rules on the server.** List every security, billing or data-integrity rule and where the backend enforces it. The UI hiding something doesn't count.
   *In this epic:* {{CL_SERVER_RULES}}
   <!-- FILL: every rule from the decisions and acceptance criteria that a user could get around if only the UI enforced it: secrets shown once, permissions, limits, money, anything "immediately". -->
6. **Make failures visible.** Name the failure modes and the log line, metric or alert for each, so an operator can see them.
   *In this epic:* {{CL_FAILURES}}
   <!-- FILL: the failure states in the prototype and tests (error screens, rollbacks, partial operations), each as a failure mode to log or measure. -->
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
    *In this epic:* {{CL_HARD_PARTS}}
    <!-- FILL: the components this epic is known to change (from the description and a read of the code), so the tech lead starts the table from them. Don't answer the questions here; the tech lead does, from the code. -->
11. **Check every assumption about the data.** List each thing the plan assumes about stored data: which values exist, what's unique, ranges, counts, which environment has what. Check each one with a read-only query in the environment that matters (usually production), and record the query and its result. If you can't run it there, write the query for {{REVIEWER}} to run, and treat the assumption as an open question until the result is in.
    *In this epic:* {{CL_DATA_ASSUMPTIONS}}
    <!-- FILL: the data facts the epic's decisions already rest on, with the query or comment each came from, and any the shaping conversation assumed without checking. -->
---

## 4. Stop for approval

When the plan is committed, stop. Reply to {{REVIEWER}} with:
- the plan's path and the stack name (or, unstacked, the plan's branch and PR)
- a summary of the plan: for each story, the tasks in each repo and their order
- the "Current state" findings, the blockers and the open questions
- anything in the code that contradicts the decisions in section 1, quoted with its file and line
- any contradiction inside the plan itself (checklist item 9)
- the "Hard parts" table and the pre-mortem (checklist item 10)
- each data assumption with its query and result, and any query {{REVIEWER}} must run (checklist item 11)
- for each branch, the callers it reaches outside its own subsystem (checklist item 7)
- the **Rollout needed** line from checklist item 4

**Do not post any Jira comments until {{REVIEWER}} approves the plan.** If they ask for changes, update the plan, commit it, and stop again.

---

## 5. After approval: post kickoff comments on each story

**First, if the plan says Rollout needed: yes,** set up the deploy work so it can't be missed:
- Find the epic's deploy ticket: a Task under {{EPIC_KEY}} whose title starts with `Deploy {{EPIC_KEY}}`. Create it only if there's none, titled `Deploy {{EPIC_KEY}} ({{EPIC_TITLE}}) to staging and production`. Either way, make sure its Components are set. Never make a second one.
- Use the `write-runbook` skill for the rollout in the plan, on that ticket. It writes the runbook in `docs/runbooks/`, with one sub-task of the deploy ticket for each of its stages. The code doesn't exist yet, so this runbook is a **draft**: say so at its top, get the stages and their sub-tasks right, and write each command as far as the plan allows. The commands are checked against the finished code before release.
- Name the deploy ticket and the runbook in the Release order comment below.

For each of {{STORY_KEYS}}, add one Jira comment per repo that has work in the story. Skip a repo with no work.

{{KICKOFF_TITLES}}
<!-- FILL: one line per repo the epic touches, in order, as "**<name>:** title it `<kickoff_title>`; its branch suffix is `<branch_suffix>`." -->

Each comment is a self-contained prompt for a separate coding agent. Write it so the agent needs nothing else. It must include:

1. **Order:** where this repo comes in the story's order. If it depends on another repo that has work in the story, say: "Do not start until the branch `<name>` in `<that repo>` is merged (into the stack, when stacked). It provides `<endpoint/field>`."
2. **Branch:** <!-- IF NOT STACKED -->"Create a new branch from `main` for this work, and open its PR against `main`." Give the branch name, `<story key>-<the repo's branch_suffix>`, and, if it needs another branch's code, say "start once `<branch>` has merged". Add: "{{PR_TITLE_RULE}} Don't write cross-repo dependency notes into the PR; add this branch to the epic's Release order comment instead."<!-- END IF NOT STACKED --><!-- IF STACKED -->"Create a new branch for this work and add it to the stack for its deploy (see `gh stack --help`)." Name that stack: `{{STACK_NAME}}` for the first deploy, and for a later deploy the stack its first branch started (record each deploy's stack in the Release order comment). Give the branch name, `<story key>-<the repo's branch_suffix>`, and the branch it stacks on. If this branch is in the **same deploy** as the branch below it, say "stacked on `<branch>`". If it's the **first branch of a new deploy**, say "start a new stack for Deploy <N>: base it on `<earlier deploy's top branch>` but don't link it into that stack" (see `stacked-prs`, One deploy per stack). Add: "{{PR_TITLE_RULE}} Don't write cross-repo dependency notes into the PR; add this branch to the epic's Release order comment instead."<!-- END IF STACKED -->
3. **Plan section:** the path to the plan, and which section to execute with the {{EXECUTE_SKILL}} skill.
4. **Scope fence. Copy this word for word:**
   > You are the **[repo name]** agent. Change only **[repo name]**. Do not edit any other repo, even for a "quick" fix. If you find you need a change on the other side, stop, write down exactly what you need, and leave it for the other agent.
5. **E2E tests:** which Xray test IDs and scenarios to automate at this level of the stack, and which belong to the other layer. If none apply at this level, say "none". {{FLAG_STATE}}
   <!-- FILL: "Don't name flag tags (<stack.flag_tags>) from memory: tag the scenarios for the local stack's real flag state (check with `<stack.flag_state>`)." -->
6. **Testing:** "The Jira e2e tests are the minimum, not the whole job. Write unit tests for every new or changed function, test-first, plus integration tests where code crosses a boundary (database, third-party service, HTTP). Run the full relevant test suite before you open the PR."
7. **Artifacts:** name the exact artifacts and sections the agent should open. Use the Jira attachment names first and the live links second.
   <!-- IF UI -->
   - **Comments for a repo with UI:** the prototype screen and states for this story (from the table in section 1), the matching slice card in the build guide, and the design-system pattern to follow.
   - **Other comments:** the slice card in the build guide, plus the prototype state that shows the behavior the repo must support, or the section of the design doc it builds.
   <!-- END IF UI -->
   <!-- IF NO UI -->
   - **Every comment:** the slice card in the build guide, and the sections of the design doc (its decisions and diagrams) that this branch builds.
   <!-- END IF NO UI -->
8. **Contract:** the endpoints and shapes from the plan that this branch produces or consumes. A comment for a repo with a `contract` must include it word for word:
   {{CONTRACTS}}
   <!-- FILL: the name and `contract` of each repo the epic touches that has one. -->
9. **Local stack,** in comments for {{LOCAL_STACK_REPOS}} only: {{LOCAL_STACK}}
   <!-- FILL: LOCAL_STACK_REPOS names each touched repo that uses the local stack (every one without `local_stack: false`). If none does, or the config has no `stack`, delete this item. -->
   <!-- FILL: "<stack.how> (for example <stack.extra_resources>). Never use <stack.never>. Local runs use the local database your roost config names for the machine you're on (`stack.database.local`; load it with `roost-config`), which may not be the shared one, so never pass another database's address to a command; after adding a migration, the agent for the repo that owns migrations applies it there with `<stack.database.apply_migrations>` and checks it with one call that touches the new schema." When `deploy.migrations_run_on_deploy` is false, add: "Every new migration also goes on the epic's deploy ticket (the Migrations to apply comment and pre-deploy sub-tasks in `stacked-prs`); add the note if it isn't there." Leave out what the config doesn't have. -->
{{APPLY_GATE_ITEM}}
   <!-- FILL: for each repo the epic touches that has `apply_gate`, an item for its comments only: "**Plan and apply:** run `<apply_gate.plan>` and post the plan in the PR, again after every push that changes it. Never run `<apply_gate.apply>` yourself<, unless the orchestrator tells you {{REVIEWER}} approved that exact plan, when apply_gate.who is agent_after_approval>. The plan is applied <before the PR merges | after it merges>, and the branch is done when the apply is recorded and a fresh plan shows no changes." Delete this line if no touched repo has `apply_gate`. -->
10. **Only ask for what the agent can do.** Don't require steps a coding agent can't do (for example attaching images to a PR). Screenshots go on the story's Jira issue, linked from the PR.
11. **Rules and tests:** in every comment, include the checklist item 10 rules for the components this branch changes, each with a test that proves it. Comments for repos with server code must also include the checklist item 5 server-side rules, each with a test that proves it.
12. **Failure visibility (repos with server code only):** the logs and metrics from checklist item 6 that this branch adds.
13. **Definition of done:** the story's acceptance criteria, and that all tests pass.
14. **Review each task as it's done. Copy this word for word:**
    > After each task in the plan, before starting the next, review that task's changes: run `/code-review` on its commits, or have a fresh-context reviewer read them. Check each finding against the code, fix the real ones test-first, and say which you dismissed and why, citing file and line. Then ask: **what else in the code does the same job?** Search for code with the same interface, base class, naming or pattern. Change it the same way, or record why it stays different. Don't leave the review to the end of the branch: a fix reviewed only at the end can break the next fix.
15. **Evidence in reports:** "Every claim about the code or data in your reports cites its file and line, or the query you ran and its result. Write "unknown" for anything you didn't check; never a guess."

Then post one **Release order** comment on the epic: a table of every branch and PR in deploy order across every repo, with a **Deploy** column, and what each waits for. Keep it current as PRs open.

---

## 6. Report back

When the comments are posted, reply with a table with one row per story: a column per repo saying whether its kickoff comment was posted (yes or no), and the order. If the rollout needed a deploy ticket, also give its key, its sub-tasks and the runbook's path.

Don't change anything in Jira other than the comments, and the deploy ticket and its sub-tasks, described in section 5.
```

---

## Reference example

If the config has `planning.reference_prompt`, read it to see how detailed a filled-in "In this epic" line should be.
