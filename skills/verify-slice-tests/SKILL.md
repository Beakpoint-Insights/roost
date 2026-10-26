---
name: verify-slice-tests
description: After a slice's changes are pushed, prove which of its story's Xray tests are automated and passing, label and close those, and propose splits for tests with scenarios that aren't automated, waiting for the user's answer. Reports one table and fixes nothing. Use when the user asks which tests for a story are automated, to "verify the tests for PROJ-X", or to label and close a slice's tests. To write missing automation instead, use automate-xray-tests.
---

# Verify Slice Tests

The changes for a story are pushed. Prove which of its Xray tests are automated and passing, label and close the ones that are, and for tests only partly automated, propose a split and wait.

**First, load the team config with `roost-config`,** and read its Xray adapter notes (`references/tests-xray.md`).

**Input:** the story key. Everything below calls it STORY.

## Scope

- The tests in scope are the Xray Test issues linked to STORY with the `tests.xray.test_link_type` link type (the test is the inward issue, the story the outward one), except retired tests (resolution `Won't Do`; see the Xray adapter notes). Nothing else.
- **Manual tests** (labelled `tests.manual_label`; see "Manual tests" in the Xray adapter notes) are in scope, but nothing here looks for automation for them: they're checked by their recorded run (step 2).
- Don't report on tests linked to other stories, and don't say when other tests are scheduled. If a test is linked to STORY, it's in scope, even if another story's work is needed to make it pass.

## Steps

1. **List the tests.** Read STORY's issue links and collect every linked Test issue.
2. **Read each test's scenarios** through the Xray GraphQL API, as the Xray adapter notes show (`getTests` with the test's key; credentials in `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET`). Each `Scenario:` is one unit you must account for, matched by its exact name.
   - **For a manual test,** read its `manual run:` comments instead, and skip steps 3 and 4 for it. Its status is **Manual: passed** (the newest run passed every scenario), **Manual: failed** (the newest run failed one; name it), **Manual: not run yet**, or **Manual: after release** (its description says `When: after release` and it hasn't been run).
3. **Find the automation for each scenario** of every other test. Search every repo in `repos`:
   - The e2e repo: Cucumber feature files in `e2e.scenarios_dir` tagged with the test's key (`e2e.tag_style`), with a scenario of the same name.
   - Other repos: a scenario marked `e2e.backend_marker` counts only if its comment names a test that exists in another repo, and that test's assertions match the scenario.
   - A scenario with no matching automation is "not automated". Don't call anything "partially covered".
4. **Run the automation now,** against the commit that was pushed. Don't rely on CI or an earlier run. Run each e2e feature by tag (`e2e.run_tags`), and each backend test by its fully qualified name.
5. **Work out each test's status** from its scenarios:
   - **Automated and passing:** every scenario has automation, and all of it passed in this run.
   - **Automated and partially passing:** every scenario has automation, and some of it failed.
   - **Automated and failing:** every scenario has automation, and all of it failed.
   - **Not automated:** at least one scenario has no automation.
   - **Couldn't run:** the automation exists but couldn't be run here. Say why in one line. Never guess a result. A scenario that skips because its flag tags don't match the local stack's flag state counts here; name the tag and the actual flag value.
6. **Label and close the tests that are Automated and passing,** and close each **Manual: passed** test that isn't Done yet (no label):
   - Automated tests only: add the label `tests.automated_label`, keeping any existing labels.
   - Move the test to `tracker.statuses.done`.
   - Change nothing on any other test. If a test already has the automated label but isn't passing now, leave it as it is and flag it in the table.
7. **Propose a split for each Not automated test whose automated scenarios all passed.** Never for a manual test. Some scenarios are things the user doesn't want automated. Don't decide that yourself, and don't change the test yet. For each such test, show:
   - **What isn't automated:** each scenario with no automation, or the steps of a scenario that the automation doesn't check, with the reason (for example, it needs a real external service).
   - **The proposed split:**
     - The **existing test** keeps every automated scenario. A scenario that's only partly automated becomes the part the automation checks. Show its new Gherkin in full.
     - A **new Xray Test** gets the part that isn't automated. Show its summary and its full Gherkin.
   - Then ask: "Split as proposed, change the split, or automate the rest instead?" **Stop and wait for the answer** before touching that test.
8. **If the user approves a split:**
   - **Before overwriting anything,** read the existing test's Gherkin and save a copy to a local file. Say where it is.
   - Update the existing test's Gherkin (Xray `updateGherkinTestDefinition`, or the `create-xray-test` skill's update steps). Then update the feature file so its scenario text matches the new Xray text word for word. Re-run it, and push the change.
   - Create the new Xray Test with the `create-xray-test` skill. Set the same Components as the existing test, and link it to STORY with the `tests.xray.test_link_type` link type.
   - The **existing test**, now fully automated and passing: add the automated label and move it to `tracker.statuses.done`.
   - The **new test:** move it to `tracker.statuses.done`. **Don't** add the automated label.
9. **Re-read the tracker** after your changes, so the table shows each test's real label and status, not what you meant to set.

## Output

One table, then the details. Nothing else.

| Test | Summary | Scenarios automated | Result | Automated label | Status |
|---|---|---|---|---|---|
| PROJ-XXXX | … | 4 of 4 | Automated and passing | Yes | Done |

For a manual test, "Scenarios automated" is "manual" and "Result" is its manual status, with the date of the run it comes from.

Under the table, for each test that isn't **Automated and passing** or **Manual: passed**:
- **Failing:** the scenario name, the test that failed (file and test name), and the first line of the assertion error.
- **Not automated:** the scenario names that have no automation, plus the proposed split from step 7.
- **Couldn't run:** what stopped you.
- **Manual: failed** or **not run yet:** what its description says to run, and where, so the owning session or the user can run it. **After release:** one line saying it's left for after release.
- **Label mismatch:** any test with the automated label that isn't passing.

After the user answers about a split, carry it out and print the table again.

Don't fix failing tests while doing this. Report what you find.
