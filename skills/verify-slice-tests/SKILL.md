---
name: verify-slice-tests
description: After a slice's changes are pushed, prove which of its story's tests are automated and passing, mark those automated, and propose splits for tests with scenarios that aren't automated, waiting for the user's answer. Reports one table and fixes nothing. Use when the user asks which tests for a story are automated, to "verify the tests for PROJ-X", or to mark a slice's tests automated. To write missing automation instead, use automate-xray-tests.
---

# Verify Slice Tests

The changes for a story are pushed. Prove which of its tests are automated and passing, mark the ones that are, and for tests only partly automated, propose a split and wait.

**First, load the team config with `roost-config`,** and read its tests adapter (`tests.kind`). Each step below names one of the adapter's operations ("A story's tests", "Run a test", …); the adapter says how to do it with this team's tests.

**Input:** the story key. Everything below calls it STORY.

## Scope

- The tests in scope are STORY's tests ("A story's tests"), except retired ones ("Retire a test"). Nothing else.
- **Manual tests,** if the adapter has them ("Manual tests"), are in scope, but nothing here looks for automation for them: they're checked by their recorded run (step 2).
- Don't report on other stories' tests, and don't say when other tests are scheduled. If a test is STORY's, it's in scope, even if another story's work is needed to make it pass.

## Steps

1. **List the tests** ("A story's tests").
2. **Read each test's scenarios** ("Read a test's scenarios"). Each scenario is one unit you must account for, matched by its exact name.
   - **For a manual test,** read its `manual run:` comments instead, and skip steps 3 and 4 for it. Its status is **Manual: passed** (the newest run passed every scenario), **Manual: failed** (the newest run failed one; name it), **Manual: not run yet**, or **Manual: after release** (its description says `When: after release` and it hasn't been run).
3. **Find the automation for each scenario** of every other test ("Find a scenario's automation"), in every repo in `repos`. A scenario with none is "not automated". Don't call anything "partially covered".
4. **Run the automation now,** against the commit that was pushed ("Run a test"). Don't rely on CI or an earlier run.
5. **Work out each test's status** from its scenarios:
   - **Automated and passing:** every scenario has automation, and all of it passed in this run.
   - **Automated and partially passing:** every scenario has automation, and some of it failed.
   - **Automated and failing:** every scenario has automation, and all of it failed.
   - **Not automated:** at least one scenario has no automation (for a test that only exists as a draft, say "not written").
   - **Couldn't run:** the automation exists but couldn't be run here. Say why in one line. Never guess a result. A scenario that skips because its flag tags don't match the local stack's flag state counts here; name the tag and the actual flag value.
6. **Mark the tests that are Automated and passing** ("Mark a test automated"), and close each **Manual: passed** test that isn't closed yet (without marking it automated). Change nothing on any other test. If a test is already marked automated but isn't passing now, leave it as it is and flag it in the table.
7. **Propose a split for each Not automated test whose automated scenarios all passed.** Never for a manual test. Some scenarios are things the user doesn't want automated. Don't decide that yourself, and don't change the test yet. For each such test, show:
   - **What isn't automated:** each scenario with no automation, or the steps of a scenario that the automation doesn't check, with the reason (for example, it needs a real external service).
   - **The proposed split** ("Split a test"): the existing test keeps every automated scenario (a scenario that's only partly automated becomes the part the automation checks), and a new test gets the part that isn't automated. Show both in full.
   - Then ask: "Split as proposed, change the split, or automate the rest instead?" **Stop and wait for the answer** before touching that test.
8. **If the user approves a split,** carry it out as "Split a test" says, saving the existing test's scenarios to a local file first and saying where ("Update a test's scenarios"). Re-run the existing test, push any change, and mark it automated; the new test isn't marked automated.
9. **Read the tests back** after your changes, so the table shows each test's real state, not what you meant to set.

## Output

One table, then the details. Nothing else.

| Test | Summary | Scenarios automated | Result | Marked automated |
|---|---|---|---|---|
| PROJ-XXXX | … | 4 of 4 | Automated and passing | Yes |

For a manual test, "Scenarios automated" is "manual" and "Result" is its manual status, with the date of the run it comes from.

Under the table, for each test that isn't **Automated and passing** or **Manual: passed**:
- **Failing:** the scenario name, the test that failed (file and test name), and the first line of the assertion error (or, for a graded case, the grader and its verdict).
- **Not automated:** the scenario names that have no automation, plus the proposed split from step 7.
- **Couldn't run:** what stopped you.
- **Manual: failed** or **not run yet:** what its description says to run, and where, so the owning session or the user can run it. **After release:** one line saying it's left for after release.
- **Marked but failing:** any test marked automated that isn't passing.

After the user answers about a split, carry it out and print the table again.

Don't fix failing tests while doing this. Report what you find.
