---
name: automate-xray-tests
description: Automate the Xray Cucumber tests linked to a story or slice. Read each test's Gherkin from the Xray API, find which scenarios already have automation, write the missing tests at the right layer, run them, and only when every scenario passes label the test `automated` and move it to Done. Use when a developer agent is asked to "automate the tests for PROJ-X", "figure out why these tests aren't automated", or to finish the e2e work for a slice.
---

# Automate Xray Tests

The Xray Gherkin is the spec. Your job is to make every scenario in it run as an automated test, or to say exactly why one can't.

**First, load the team config with `roost-config`,** and read its Xray adapter notes (`references/tests-xray.md`).

**Leave manual tests alone.** A test labelled `tests.manual_label` is run by hand on purpose and closes on a recorded run (see "Manual tests" in the Xray adapter notes). Don't write automation for it, don't propose splitting it, and don't count it as missing automation; list it in the report as "manual".

**With `tests.kind: evals`,** this team's tests are eval cases in the repo: follow this skill's row in "In each skill" in `roost-config`'s `references/tests-evals.md` instead of the Xray steps below.

## Inputs

- The test keys, or the story whose linked tests to cover (link type `tests.xray.test_link_type`: the test is inward, the story outward).
- The branch to work on. Use the one checked out unless told otherwise.
- Any notes on which scenarios the other repo already automates.

## 1. Read the scenarios through the Xray API

The tracker description of a Test is empty; the scenarios live in Xray. Read them with Xray's GraphQL API (`getTests`, as the Xray adapter notes show), which is more reliable than the browser editor. Credentials are the `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` environment variables. Never print them.

## 2. Map every scenario

For each test, list each `Scenario:` by name with:
- **Where it's automated, if anywhere:** Cucumber feature files in the e2e repo tagged with the test's key (`e2e.tag_style`; match what the repo's existing features use), or a test in another repo named in an `e2e.backend_marker` comment.
- **Its latest result,** from a run you do now, not CI history. Check whether CI actually skips it (a test against a live outside service, skipped in CI, isn't passing in CI).

## 3. Write what's missing

- Put each scenario at the layer that can really prove it. Behaviour the browser can't see (a database row, an email not sent, a token never logged) belongs in the backend's tests; write the UI scenario verbatim with `e2e.backend_marker` and a comment naming the backend test.
- Follow the repo's conventions: feature and steps files under `e2e.scenarios_dir`, the test's key as `e2e.tag_style` says, and the flag tags (`stack.flag_tags` and similar) so gated scenarios skip in the wrong flag state. Choose the tags from the local stack's real flag state (`stack.flag_state`), not from the kickoff text; if they differ, say so in the PR.
- Start or stop parts of the local stack yourself when a test needs them, as `stack.how` says (never `stack.never`).
- Drive through the real app on the services in `stack.services`. Stub network calls only where the scenario itself describes a stubbed state (a pending or failing request, a 403 the clock would produce).
- Use the test helpers the suite already has (for example `e2e.helpers_hint`) before writing new ones.

## 4. Knowledge goes in the repo, not your memory

These tests run in CI and on teammates' machines. When something blocks a scenario (a missing capability, an unbuilt slice, a bug), tag it `@skip` in the feature file with a comment giving the reason and the ticket. Setup knowledge (how to create a fixture, which flag state a scenario needs) also goes in comments next to the scenario.

## 5. When the shipped behaviour differs from the Gherkin

Don't edit a scenario to make a test pass. Only when the behaviour deliberately differs (a decision changed it), update the Gherkin in Xray with `updateGherkinTestDefinition` (the Xray adapter notes show it), and tell the user why.

Save the old Gherkin to a local file before replacing it, and say where it is. If a scenario should be split because part of it won't be automated, propose the split and wait for the user's answer.

## 6. Label and close only when everything passes

Add the `tests.automated_label` label and move the test to `tracker.statuses.done` only when every scenario has automation that passed in your run, at either layer. If any scenario is skipped, pending, gated by an unbuilt slice, or a no-op with no backend test, leave the ticket open and unlabelled. Set Components on each test as you finish it.

## 7. Report

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then start with the outcome: "4 of 6 tests automated and closed; 2 blocked." Then one table:

| Test | Scenarios automated | Result | Label | Status | If not done, why |
|---|---|---|---|---|---|

Say plainly what passed and what didn't. List anything you couldn't automate and why.
