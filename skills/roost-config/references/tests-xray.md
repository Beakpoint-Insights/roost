# Test adapter: Xray

How tests work when `tests.kind` is `xray`. The tracker is Jira (see `tracker-jira.md`). The skills say *what* to do with a story's tests ("read its scenarios", "mark it automated"); the operations below say *how*, with Xray.

## In a prompt

A prompt that must stand alone (the tech lead prompt) introduces the tests as: "The Xray tests linked to each story. Their Cucumber scenarios are in the Xray “Test details” panel. If you can't read that panel, use the test summaries in the build guide."

## Operations

| Operation | With Xray |
|---|---|
| **A story's tests** | The Test issues linked to the story with `tests.xray.test_link_type` (the test inward, the story outward), except retired ones ("Retiring a test"). |
| **Read a test's scenarios** | Through the Xray API ("Reading and updating scenarios"): its Gherkin, one unit per `Scenario:`, with its Preconditions. |
| **Find a scenario's automation** | A Cucumber feature file in the e2e repo's `e2e.scenarios_dir`, tagged with the test's key (`e2e.tag_style`), with a scenario of the same name; or a scenario marked `e2e.backend_marker` whose comment names a test that exists in another repo and whose assertions match. |
| **Run a test** | Each e2e feature by tag (`e2e.run_tags`), each backend test by its fully qualified name, on the commit under test. |
| **Mark a test automated** | Add `tests.automated_label` (keeping its other labels) and move it to `tracker.statuses.done`. Never add scenarios to a test that's already marked. |
| **Write scenarios** | Cucumber scenarios, in the Gherkin style guide in the `live-verified-bdd` skill, with Xray's rules ("Gherkin for Xray"): no `Feature:` line, no `Background:`. |
| **Unmark a test** | A test marked automated that fails now: remove `tests.automated_label` and move it back to `tracker.statuses.todo`. |
| **Create a test** | The `create-xray-test` skill ("Creating tests"). |
| **Update a test's scenarios** | Save the current Gherkin to a local file first, then `updateGherkinTestDefinition`, then update the feature file so its scenario text matches word for word ("Reading and updating scenarios"). |
| **Split a test** | The existing test keeps the automated scenarios (a partly automated one becomes the part the automation checks); a new test, created with `create-xray-test`, with the same Components and story link, gets the rest, and is moved to done without the automated label. |
| **Retire a test** | "Retiring a test". |
| **Shared setup** | A Precondition ("Shared setup: Preconditions, not `Background:`"). It's part of the tests, not work: never an open ticket. |
| **Manual tests** | "Manual tests", when the config has `tests.manual_label`. |

## What a test is

- Each test is a Jira issue of type **Test**, with Cucumber scenarios in Xray's "Test details" panel. The issue's description is empty; the scenarios live in Xray.
- A test's parent is the epic. It's linked to its story with `tests.xray.test_link_type` (the test is the inward issue, the story the outward one). A cross-cutting test, one that needs several slices to pass, is linked to the last story it depends on, and takes that story's Components.
- **Automated** means every scenario in the test has automation that passed in a run you did, at the UI or backend layer. Only then does the test get the `tests.automated_label` label and move to `tracker.statuses.done`. A test that's Done without the label was split on purpose (`verify-slice-tests`) and has no automation by design, or is a manual test (below).
- Never add scenarios to a test that already has the automated label and is Done; that would make the label false. Create a new test instead.

## Reading and updating scenarios: the Xray API

Credentials are the `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` environment variables. Never print them.

```bash
TOKEN=$(curl -s -H 'Content-Type: application/json' -X POST https://xray.cloud.getxray.app/api/v2/authenticate \
  -d "{\"client_id\":\"$XRAY_CLIENT_ID\",\"client_secret\":\"$XRAY_CLIENT_SECRET\"}" | tr -d '"')
curl -s -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -X POST https://xray.cloud.getxray.app/api/v2/graphql \
  -d '{"query":"{ getTests(jql: \"key = PROJ-1234\", limit: 1) { results { issueId gherkin jira(fields: [\"summary\",\"labels\",\"components\",\"status\"]) preconditions(limit: 10) { results { issueId definition jira(fields: [\"key\"]) } } } } }"}'
```

To replace a test's scenarios:

```graphql
mutation($id: String!, $g: String!) { updateGherkinTestDefinition(issueId: $id, gherkin: $g) { issueId gherkin } }
```

**A test's scenarios aren't complete without its Preconditions.** The `preconditions` in the result hold the shared Given steps (the identity, the tenant, the starting page) that run before every scenario. Automating or verifying a test means automating or checking it with those steps applied, the way Xray exports them, as the feature's Background.

**Before replacing scenarios,** save the current Gherkin to a local file and say where it is. Afterwards, read it back and compare.

Without the credentials, use the browser steps in the `create-xray-test` skill.

## Creating tests

Use the `create-xray-test` skill. When `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set, it creates tests through the API (below); otherwise it uses the browser. Either way it sets the parent, Components and labels, links the story, and checks what was saved.

```graphql
mutation($t: UpdateTestTypeInput!, $g: String!, $p: [String], $j: JSON!) {
  createTest(testType: $t, gherkin: $g, preconditionIssueIds: $p, jira: $j) { test { issueId jira(fields: ["key"]) } warnings }
}
```

with `t = {"name": "Cucumber"}`, `p` the Precondition issue IDs (or `[]`), and `j = {"fields": {"summary": …, "project": {"key": …}, "parent": {"key": <EPIC>}, "components": [{"id": …}], "labels": […], "description": …}}`. `labels` and `description` are for manual tests (below); leave them out otherwise. Read each test back with `getTests` and compare its Gherkin with what you sent. Link it to its story through the tracker afterwards.

## Shared setup: Preconditions, not `Background:`

Xray doesn't accept a `Background:` inside a test. Steps several tests share (for example "Given I am signed in as a tenant admin") become an Xray **Precondition**, created once and attached to each test that needs it. Xray exports it as the feature's Background.

```graphql
mutation($t: UpdatePreconditionTypeInput!, $d: String!, $j: JSON!) {
  createPrecondition(preconditionType: $t, definition: $d, jira: $j) { precondition { issueId jira(fields: ["key"]) } warnings }
}
```

with `t = {"name": "Cucumber"}`, `d` the Given steps, and `j` the same fields as a test (the epic as parent). Reuse an existing Precondition with the same steps before creating one.

**A Precondition is part of the epic's tests, not work.** Leave it out of open-ticket counts, carry-over sorting and close-out. Close it (`tracker.statuses.done`) when the last test that uses it is done.

## Tests only for what a suite can check, or a person runs on purpose

File an Xray test for behaviour an automated suite in one of the `repos` can check before release: the browser e2e suite, or a backend test the scenario points to (`e2e.backend_marker`). Backend-only behaviour gets Xray tests too. Work no suite can prove before release, such as a docs page that's published only at release, in a repo whose `tests` are a build and a preview, gets none: its story's acceptance criteria are its checks, verified on the PR (its build and preview) with evidence.

The one exception is a **manual test**, and only when the config has `tests.manual_label`. Without that key, never file a `@manual` test, or one that can only pass after release: it can never be labelled automated, so the slice can never finish.

## Manual tests

Some checks are one-off on purpose: they're run once, by hand, against a real environment, and automating them would cost more than it proves ("`tofu plan` shows no changes", "the old provider's invoice is zero"). When the config has `tests.manual_label`, such a check is a manual test:

- **Labelled** `tests.manual_label`, decided while shaping (`shape-epic` phase 5), never later to get out of automating something.
- **Its description says how to run it:** the environment, the steps or commands, and what passing looks like. Add a line `When: after release` if it can only pass after the epic ships; otherwise it's run in its story's slice.
- **All manual or all automated.** A test never mixes the two; a check that's partly automatable becomes two tests.
- **Closed by a recorded run, not by automation.** Whoever runs it adds a comment starting `manual run:` with the date, who ran it, the environment, a pass or fail for each scenario, and the evidence (command output, a link, a screenshot attached to the ticket). When every scenario passes, move the test to `tracker.statuses.done`. It never gets `tests.automated_label`.
- **Who runs it:** the session of the repo that owns the story's work runs the checks it can make read-only. Anything that changes a shared or production resource, needs access the session doesn't have, or is in `deploy.runbooks.never_run_against`, goes to the user as a 🙋 **Your turn** action, with the steps from the description; the session records the run from their answer.
- **Not automated, ever:** no skill reports a manual test as "not automated", proposes splitting it, or writes automation for it. It's run once: once it's Done, later slices don't run it again.
- **After release:** a manual test with `When: after release` isn't part of any slice. Like a person-owned task, it stays open under the epic, is listed with the user as its owner, and the release call doesn't wait for it.

## Retiring a test

A test that's no longer wanted is **retired**: moved to `tracker.statuses.done` with the resolution `Won't Do` (Xray Test issues usually have no Won't Do status), with a comment saying why. Keep its story link for history. Every skill leaves retired tests out: they're not checked, labelled, split, counted or carried over.

## Gherkin for Xray

- **No `Feature:` line.** Xray builds the feature from the test's summary. Start with `Scenario:`.
- **No `Background:`.** Put shared setup in a Precondition (above).
- Scenarios are matched to automation by their exact name.
- The automation tags each feature with the test's key, in the e2e repo's `repos[].e2e.tag_style`.
