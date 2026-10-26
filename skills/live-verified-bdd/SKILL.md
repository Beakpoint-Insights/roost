---
name: live-verified-bdd
description: Write or revise Cucumber scenarios for a feature that already runs, then walk each one in the live app with Playwright and correct it to match what the app does. Use to write test scenarios, or to check that existing scenarios still match the app. Doesn't file anything in the tracker; hand the result to create-xray-test. For a new epic that isn't built yet, use shape-epic.
---

# Live-Verified BDD Test Writing

Write Cucumber/Gherkin scenarios and check each one in the running app before calling them done. Every scenario is walked through in the browser with Playwright. The app is the source of truth, not the code.

## When to Use

- Writing scenarios for a feature that already runs
- Checking that existing scenarios still match what the app does
- The user says "write tests", "BDD", "Cucumber", "Gherkin" or "E2E test cases" for something that's built

## When Not to Use

- **Filing scenarios as the team's tests:** the tests adapter's "Create a test" does that. This skill hands off to it at the end.
- **A new epic that isn't built yet:** there's no app to check against. `shape-epic` writes those scenarios from the prototype.

This file holds the Gherkin style guide that the other skills follow.

**First, load the team config with `roost-config`.** `stack.services` gives the app's URLs, and `qa.test_account_email` the pattern for test accounts.

## Workflow

### Phase 1: Gather Context

Ask the user for:
1. **What to test** — feature name, ticket, or area of the app
2. **Scope** — which vendors/entities/flows to include (avoid testing everything)
3. **Credentials** — real credentials for live connection testing if applicable
4. **URLs** — only if `stack.services` doesn't already give them
5. **Test user** — username/password for the test account

Read the relevant code to understand:
- Domain entities and their properties
- Controller endpoints and authorization policies
- Value objects, enums, and configuration descriptors
- Handler validation logic and error paths

### Phase 2: Draft Gherkin from Code

Write declarative Gherkin scenarios organized by feature:
- **Background** for shared preconditions (signed in, tenant context). When the team's tests can't hold a `Background:`, the setup goes where the tests adapter's "Shared setup" says
- **Given-When-Then** with business language — no CSS selectors, no API paths
- **Data tables** for field listings (`| field | required |`)
- **Tags**: `@smoke` for critical paths, `@authorization` for auth tests
- **One behavior per scenario** — if something validates AND advances, split them
- **Scenario Outline + Examples** only for true variations of the same behavior

### Phase 3: Verify Every Scenario in the Live App

This is the critical differentiator. If a scenario needs data the app doesn't have yet, load it first with `stack.test_data` (local stack only), and say in the summary what you loaded. For EACH scenario:

1. Open the app in Playwright (`browser_navigate`)
2. Perform each Given/When step literally in the UI
3. Use `browser_snapshot` to check each Then assertion against actual UI state
4. Record every discrepancy — expected vs. actual

Common things that diverge from code reading:
- Wizard steps that validate before advancing (not just navigate)
- Client-side validation messages (not visible in backend code)
- Exact field labels, placeholder text, and help text
- Error message wording
- Redirect targets after auth actions
- UI states like badges, timestamps, loading states

### Phase 4: Revise Based on Observations

- **Update Gherkin** to match what the app actually does
- **Split scenarios** when one scenario turned out to cover multiple distinct behaviors
- **Add scenarios** for behaviors discovered during testing (validation errors, edge cases)
- **Mark untestable scenarios** (e.g., permission tests needing a different user role)
- **Remove scenarios** that proved redundant or inaccurate

### Phase 5: Present and Iterate

Present the final Gherkin with a verification summary table:

```
| # | Scenario | Status |
|---|----------|--------|
| 1 | Description | PASS / REVISED / NOT TESTABLE |
```

Explain what changed from the draft and why.

### Phase 6: Hand Off for Filing

When the user approves the scenarios, ask whether to file them. If yes, file them as the tests adapter's "Create a test" says, following its "Write scenarios" rules, with:
- the epic key, and the story key for each test
- each test's title and its scenarios
- for scenarios that replace an existing test's, that test's key, so it's updated ("Update a test's scenarios") instead of a new one created

Leave out scenarios marked NOT TESTABLE unless the user says to file them.

## Gherkin Style Guide

```gherkin
# DO: Declarative, business-focused
Scenario: Vendor setup wizard validates before advancing
  When I click "Add Another" for "ClickHouse Cloud"
  And I click "Next" without filling in any fields
  Then I should see validation errors for each required field

# DON'T: Imperative, implementation-focused
Scenario: Validation check
  When I click the button with data-testid "vendor-setup-btn-clickhouse"
  And I click the element "#next-btn"
  Then the div.error-message should contain "required"
```

Rules:
- No UI selectors, CSS classes, test IDs, or API paths in step text
- Use "should" for assertions: "Then I should see..."
- Name things as the user sees them: "ClickHouse Cloud" not "clickhouse" vendor type
- Use quotes for exact UI text: `"Active"`, `"Fetch Now"`, `"Preview fetch failed"`
- Keep steps at a consistent abstraction level within a scenario
- Use concrete values: "30 minutes ago", not "some time ago"
- Keep scenarios independent; none should depend on another having run
- Include performance expectations where the feature specifies them (P99 latency, page load time)
- Cover the happy path, edge cases, error states and transitions between states

## Principles

1. **The app is the authority.** If code says X but the app does Y, the Gherkin says Y.
2. **One behavior per scenario.** Don't overload.
3. **Optimize for automation AND manual testers.** A human should be able to follow every step.
4. **Test the unhappy paths.** Empty fields, invalid credentials, missing permissions, unauthenticated access.
5. **Iterate with the user.** Present one feature at a time, verify together, then move to the next.
