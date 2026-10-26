---
name: automate-xray-tests
description: Automate the tests linked to a story or slice. Read each test's scenarios, find which already have automation, write the missing automation at the right layer, run it, and only when every scenario passes mark the test automated. Use when a developer agent is asked to "automate the tests for PROJ-X", "figure out why these tests aren't automated", or to finish the e2e work for a slice.
---

# Automate Tests

A test's scenarios are the spec. Your job is to make every scenario run as an automated test, or to say exactly why one can't.

**First, load the team config with `roost-config`,** and read its tests adapter (`tests.kind`). Each step below names one of the adapter's operations ("Read a test's scenarios", "Mark a test automated", …); the adapter says how to do it with this team's tests.

**Leave manual tests alone,** if the adapter has them ("Manual tests"). A manual test is run by hand on purpose and closes on a recorded run. Don't write automation for it, don't propose splitting it, and don't count it as missing automation; list it in the report as "manual".

## Inputs

- The test keys, or the story whose tests to cover ("A story's tests").
- The branch to work on. Use the one checked out unless told otherwise.
- Any notes on which scenarios the other repo already automates.

## 1. Read the scenarios

"Read a test's scenarios", with any shared setup they depend on ("Shared setup"). Never print a credential the adapter uses.

## 2. Map every scenario

For each test, list each scenario by name with:
- **Where it's automated, if anywhere** ("Find a scenario's automation"; match what the repo's existing tests use).
- **Its latest result,** from a run you do now ("Run a test"), not CI history. Check whether CI actually skips it (a test against a live outside service, skipped in CI, isn't passing in CI).

## 3. Write what's missing

**When the test is its own automation** (an eval case, say): a test drafted on the story but not in the repo is committed first, as drafted, before the change that should make it pass; then make the change until it passes every run.

**When scenarios are automated in a repo's suite:**
- Put each scenario at the layer that can really prove it. Behaviour the browser can't see (a database row, an email not sent, a token never logged) belongs in the backend's tests; write the UI scenario verbatim with `e2e.backend_marker` and a comment naming the backend test.
- Follow the repo's conventions: feature and steps files under `e2e.scenarios_dir`, the test's key as `e2e.tag_style` says, and the flag tags (`stack.flag_tags` and similar) so gated scenarios skip in the wrong flag state. Choose the tags from the local stack's real flag state (`stack.flag_state`), not from the kickoff text; if they differ, say so in the PR.
- Start or stop parts of the local stack yourself when a test needs them, as `stack.how` says (never `stack.never`).
- Drive through the real app on the services in `stack.services`. Stub network calls only where the scenario itself describes a stubbed state (a pending or failing request, a 403 the clock would produce).
- Use the test helpers the suite already has (for example `e2e.helpers_hint`) before writing new ones.

## 4. Knowledge goes in the repo, not your memory

These tests run in CI and on teammates' machines. When something blocks a scenario (a missing capability, an unbuilt slice, a bug), mark it skipped in the repo the way its suite does (for example `@skip` in a feature file), with a comment giving the reason and the ticket. Setup knowledge (how to create a fixture, which flag state a scenario needs) also goes in comments next to the scenario.

## 5. When the shipped behaviour differs from the scenario

Don't edit a scenario to make a test pass. Only when the behaviour deliberately differs (a decision changed it), update the scenario ("Update a test's scenarios", saving the old text to a local file first and saying where), and tell the user why.

If a scenario should be split because part of it won't be automated, propose the split ("Split a test") and wait for the user's answer.

## 6. Mark it automated only when everything passes

Mark the test automated ("Mark a test automated") only when every scenario has automation that passed in your run, at any layer. If any scenario is skipped, pending, gated by an unbuilt slice, or a no-op with no backend test, leave the test unmarked. When the tracker requires Components (`tracker.components_required`), set them on each test that's a ticket as you finish it.

## 7. Report

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then start with the outcome: "4 of 6 tests automated; 2 blocked." Then one table:

| Test | Scenarios automated | Result | Marked automated | If not done, why |
|---|---|---|---|---|

Say plainly what passed and what didn't. List anything you couldn't automate and why.
