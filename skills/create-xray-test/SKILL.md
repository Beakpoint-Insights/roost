---
name: create-xray-test
description: File Cucumber scenarios you already have into Jira as Xray Test issues, or update the scenarios on an existing Xray Test, through the browser. Sets the parent epic, Components and the link to the story, and checks what was saved. Doesn't write or check scenarios; use live-verified-bdd to write them for a feature that already runs, or shape-epic for a new epic.
---

# Create Xray Test

Files Cucumber (Given/When/Then) scenarios into Jira Xray Test issues. The scenarios go in the Xray scenario editor, not the issue description.

This skill does the filing only. The scenarios come from:
- **`shape-epic`**, for a new epic. It passes the approved test plan.
- **`live-verified-bdd`**, for a feature that already runs. It passes scenarios it has checked in the app.
- **The user**, who pastes them.

If there are no scenarios yet, stop and use one of those first. Don't make scenarios up here.

**First, load the team config with `roost-config`.** This skill is the browser half of the Xray adapter (`tests.kind: xray`); the adapter's notes are in `roost-config`'s `references/tests-xray.md`.

**This skill is only for Xray.** With another `tests.kind`, don't use it: create and update tests as that tests adapter's "Create a test" and "Update a test's scenarios" say (for eval cases, `roost-config`'s `references/tests-evals.md`).

## Prerequisites

- **With `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` set:** nothing else. Use the API ("Creating tests through the API" below); no browser is needed.
- **Without them (the browser fallback):** the Playwright MCP, with the user signed in to Jira in its browser. If they aren't, navigate to `https://<tracker.jira.site>` and wait for them to sign in.

## Input

- **Epic key** (for example PROJ-1768). Every test's parent is the epic.
- **Story key for each test.** A cross-cutting test (one that needs several slices) gets the last story it depends on.
- **For a manual test** (`tests.manual_label`; see "Manual tests" in the Xray adapter notes): that it's manual, and its "how to run it" description.
- **Each test's title and its scenarios**, in Gherkin.
- For an update: the **existing test's key** and its new scenarios.

## Creating tests through the API

When `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set, create the tests and any Preconditions through Xray's API instead of the browser steps below: the Xray adapter notes (`roost-config`'s `references/tests-xray.md`) show both mutations. It's faster and steadier than the browser. Show the user the list first, as below. Put the parent, the story's Components (step 6), and for a manual test its label and description, in the `createTest` call's `jira.fields`. Read every test back with `getTests`, comparing its Gherkin, labels and Components with what you sent; then link each test to its story (step 9). Use the browser steps only without the credentials.

## Creating a test in the browser

Before creating anything, show the user the list of tests (key to be assigned, title, story, scenario names) and get approval. Then, for each test:

### 1. Open the create dialog

```
Click: css=[data-testid='atlassian-navigation--create-button']
Wait: 2 seconds for the dialog to load
```

The issue type stays "Test" after the first one in a session. If it isn't "Test", change it with the type selector.

### 2. Fill in the summary

```
Type into: css=[data-testid='issue-create-commons.common.ui.fields.base-fields.input-field.textfield']
Content: the test title (descriptive, under 100 characters)
```

### 3. Set the parent epic

The parent field only accepts epics, not stories.

```
Click: css=[data-testid='issue-create-commons.ui.pill-parent-field.parent-trigger']
Type into: css=input#parent-field
Content: the epic key
Wait: 2 seconds for search results
Click: css=#react-select-2-option-0
```

### 4. Create the issue

```
Click: css=[data-testid='issue-create-modernised.create-button']
Wait: 3 seconds
```

### 5. Get the key and open the test

```
Snapshot: css=[role='alert']
Extract: the issue key from the alert text (for example "Created Test PROJ-2281")
Click: the "View Test" link in the alert
Wait: 4 seconds for the page to load
```

### 6. Set Components

When `tracker.components_required` is true, every ticket needs Components. Copy them from the test's story (for a cross-cutting test, the last story it depends on) with the Jira MCP `editJiraIssue` tool. For a manual test, set its label and description in the same call (labels replace every label, so send them all):

```
fields: { "components": [{ "id": "<id>" }, …] }
fields: { "labels": ["<tests.manual_label>"], "description": "<how to run it>" }   // manual tests only
```

### 7. Write the scenarios

The Xray panel lives in a Connect iframe whose URL contains `all-in-one`. The Ace editor's textarea is read-only, so `fill()` doesn't work. Set the editor's value through the frame instead:

```js
const xrayFrame = page.frames().find(f => f.url().includes('all-in-one'));
await xrayFrame.locator('.ace_content').first().click(); // enter edit mode
await page.waitForTimeout(1500);
await xrayFrame.evaluate((g) => {
  window.ace.edit(document.querySelector('.ace_editor')).setValue(g, -1);
}, gherkin);
await page.waitForTimeout(500);
await xrayFrame.getByRole('button', { name: 'Confirm' }).click();
```

On a new test, if there's no editor yet, click the "Click to add a scenario definition" element (test id `gherkin-editor-view`) first.

**Never include a `Feature:` line.** Xray builds the feature from the test summary. Start directly with `Scenario:`:

```gherkin
Scenario: [what it proves]
  Given [precondition]
  When [action]
  Then [expected result]

Scenario: [another behavior]
  Given …
```

### 8. Check what was saved

Reload the page, wait about 7 seconds, read the editor's value again, and compare it with what you set:

```js
const now = await xrayFrame.evaluate(() => window.ace.edit(document.querySelector('.ace_editor')).getValue());
```

If they differ, report it. Don't retry blindly.

### 9. Link the test to its story

Use the Jira MCP `createIssueLink` tool with link type `tests.xray.test_link_type` (by default **"Test"**, "tests" / "is tested by"):
- `inwardIssue`: the test
- `outwardIssue`: the story

Read the test back afterwards. The story should appear under its links as "tests PROJ-XXXX". Link a cross-cutting test to the last story it depends on, like any other.

## Updating an existing test

If `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set, read and update scenarios through Xray's GraphQL API instead of the browser: `getTests` to read and `updateGherkinTestDefinition` to write. The Xray adapter notes show both calls. The same steps below apply: save the current text first, then check what was saved.

In the browser, the editor's visible text can look empty even when scenarios exist, so always read the value through Ace.

1. Open the test and read the current scenarios with `getValue()` (step 8's snippet).
2. **Save that text before changing anything,** to a local file the user can find, and say where it is.
3. Set the new scenarios and confirm (step 7).
4. Reload and check what was saved (step 8).
5. If scenarios moved to another test, link that test to the story too (step 9).

## Summary

After all tests are filed or updated, show:

| Test | Story | Title | Scenarios | Manual | Saved text matches |
|---|---|---|---|---|---|
| PROJ-XXXX | PROJ-YYYY | … | 3 | No | Yes |

## Troubleshooting

| Problem | Fix |
|---|---|
| The create dialog doesn't open | Wait longer, or check whether a modal is already open |
| The parent field says "No matches found" | Only epics can be parents. Link stories with step 9. |
| The Xray iframe isn't there | Wait 4+ seconds after navigating, and scroll down if needed |
| "Click to add scenario" isn't visible | The test type must be "Cucumber". Check the Test Type field in the Xray panel. |
| The editor looks empty on an existing test | Its text is still there. Read it with `getValue()`, not the page text. |
| Stale ref IDs after navigating | Take a fresh snapshot after every navigation |
| `internal:frame` selector error | Don't use CSS selectors with `internal:frame`. Use the frame API above, or refs from a snapshot. |
| Playwright says the browser is already in use | Another session holds the signed-in browser. Don't kill it: tell the user which session's work is waiting and ask them to free the browser, then retry (see "The signed-in browser" in `roost-config`) |

## Jira details

From the config: the cloud ID is `tracker.jira.cloud_id`, the Xray panel's test id is `tests.xray.panel_test_id`, and the link type is `tests.xray.test_link_type`.
