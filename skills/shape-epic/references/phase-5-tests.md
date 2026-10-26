# Phase 5: Test Definition

**Input:** Slices (stories) + the design (phase 3) showing testable behaviors.

**Goal:** Create the tests that cover every slice, in the form the team's tests take. Read the tests adapter (`tests.kind`) first: it says what a test is and how one is created ("Create a test").

## Process

1. For each slice, identify the testable behaviors by reading its acceptance criteria and reviewing the corresponding part of the design: prototype surfaces, or the design doc's target state. Behaviour an automated check can prove before release gets a test: the browser e2e suite, a backend test, an eval case. A slice whose work nothing can prove before release (for example a docs page, whose repo's `tests` are a build and a preview) gets none: its story's acceptance criteria are its checks, verified on the PR with evidence. A backend-only slice still gets tests, automated in the backend: say so in the plan, and make sure its story's acceptance criteria are specific enough to check on the PR.

2. **Decide which tests are manual,** if the tests adapter has manual tests and the config turns them on (`tests.manual_label`). A manual test is a one-off check, run by hand against a real environment, that automating would cost more than it proves: "`tofu plan` shows no changes", "the old provider's invoice is zero", "the DNS record points at the new load balancer". Recommend manual or automated for each test, with why; the user decides. Behaviour that can regress (anything a later change could break) is automated. Keep each test all manual or all automated. For each manual test, write its description: the environment, the steps or commands, what passing looks like, and `When: after release` if it can only pass once the epic ships ("Manual tests" in the tests adapter). Otherwise there are no manual tests.

3. Categorize tests:

| Category | Description | Example |
|----------|-------------|---------|
| **Slice-specific** | Only passable after its slice is built | "Health strip ingestion cell shows gradient" |
| **Cross-cutting** | Requires multiple slices to pass | "All three health signals active and diagnosable" |

4. Draft a test plan mapping tests to slices, marking each manual test:

```
Slice 2 (Error States):
  - PROJ-XXXX: Dashboard empty state
  - PROJ-XXXX: 504 query timeout handling

Slice 3 (Ingestion Health):
  - PROJ-XXXX: Ingestion gradient thresholds
  - PROJ-XXXX: Production ingest endpoint answers after the switch (manual)

Cross-cutting (linked to the last slice they depend on):
  - PROJ-XXXX: Full confidence flow
  - PROJ-XXXX: Navigation between all views
```

5. Present the test plan. Get approval before creating.

6. **Create the tests** as the tests adapter's "Create a test" says. Give it:
   - The epic key
   - The approved test plan, with each test's title and scenarios
   - The slice-to-test mapping, so each test is linked to its story (a cross-cutting test to the last story it depends on), with that story's Components where tests are tickets
   - Which tests are manual, with each one's description

## Writing Test Scenarios

Write scenarios in the form and style the tests adapter's "Write scenarios" gives, with shared setup where its "Shared setup" says. The work isn't built yet, so there's nothing to walk through live: take exact labels, values and states from the prototype instead, and exact names, commands and expected output from the design doc for work with no UI.

## Output

The epic's tests, each linked to a story, with the manual ones marked and described.
