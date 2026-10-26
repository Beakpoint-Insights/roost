---
name: release-qa
description: QA an epic before release on the local environment. Check the environment without changing it, run the browser e2e suite and sort every failure, do exploratory testing in a real browser, file reproduced bugs in the tracker, and give a release call. Use when the user asks for release QA, a bug-hunting pass, or "is this epic ready to release".
---

# Release QA

You are QA for one epic. Find out whether "ready for release" is true, and file what isn't. Don't fix anything: no edits to app or test code, no status changes on existing tickets.

**First, load the team config with `roost-config`.** You run in the session of the repo that holds the e2e suite (the one with `e2e` in `repos`).

**No app to QA in a browser?** When the config has no `stack`, or no repo with `e2e` (a plugin or a library, say), steps 1 to 3 don't apply. You run in the lead repo's session (`planning.lead_repo`) instead, and QA is:

1. **Every repo's own checks** on the epic's newest code, as each repo's `tests` says (for this plugin, for example, `claude plugin validate --strict .` and its scripts' checks).
2. **The epic's tests,** run the way the tests adapter says (for `tests.kind: evals`, every case linked to the epic's stories), and sorted as step 2 sorts failures.
3. **Each story's acceptance criteria,** checked against what the epic's merged code actually does, one row per criterion with its evidence.

Then file bugs (step 4), report (step 5) and put the report on the epic (step 6) as usual.

## Inputs

Ask in one message for anything missing:

- **The epic key.** Read its description first, especially any flow or behaviour table: that's the intended behaviour.
- **What's out of scope:** tests that target another environment, slices not built yet, and known gaps that aren't bugs.
- **Feature flags** this run expects, and their required values.
- **The label** for bugs found in this run (for example `signup-qa`).

## 1. Check the environment

Everything runs locally, on the services in `stack.services`. Don't touch staging or production.

1. Confirm every service answers. If one doesn't, start it as `stack.how` says (never `stack.never`), and start any other resource the epic needs (`stack.extra_resources`).
2. Make sure the stack has the data the epic's flows need. If it doesn't, put it there with `stack.test_data`, against the local stack only, and record what you loaded.
3. Read the flag state with `stack.flag_state`. If it isn't what this run needs, stop and say so.
4. Check required test secrets are present in the e2e repo's `e2e.secrets_file` without printing them.
5. Record the branch and short SHA of every repo in `repos`. Don't switch branches.
6. Throughout the run, if the config has `stack.telemetry`, read the stack's own errors: from `stack.owner_repo`, `stack.telemetry.logs` and `stack.telemetry.traces` (`stack.telemetry.note`). A repeating error nobody triggered on purpose is a finding, even when no test failed.

## 2. Run the e2e suite and sort every failure

Run `e2e.run_all`, with the environment variables the flag state needs. Scenarios gated off by flag tags (for example `stack.flag_tags`) skipping is expected.

Put every failed scenario in one bucket before doing anything else:

- **Product bug:** the app does the wrong thing. Reproduce it by hand in the browser; file it if it reproduces.
- **Test bug:** the app is right and the test is wrong (stale selector, timing, old expectation). Don't file; report it with the fix you'd suggest.
- **Environment problem:** something local is missing (a service, credentials, data). Missing data you can load with `stack.test_data` isn't a reason to stop: load it and re-run. Don't file; report it.
- **Flaky:** re-run that scenario alone up to twice (`e2e.run_tags` with `"@<tag>"`). If it passes, report it as flaky with the failure output.

A failure in an unrelated suite can still be this epic's regression if it happens at a step the epic changed (sign-in, for example). Check where it fails.

## 3. Explore

Use the Playwright browser tools against the app services in `stack.services`. Create throwaway accounts with the suite's email pattern (`qa.test_account_email`), never a real account.

Write charters from the epic's flows, highest release risk first: the new-user path, wrong-identity and error paths, deep links and old URLs, password and session flows, invitations, roles, and logout. Always include general hygiene on every screen the epic touches: console errors, failed network calls, redirect loops, layout at phone width, keyboard-only use, and error messages a normal person could understand. Go off-charter when something looks odd.

## 4. File bugs

Before filing, search for duplicates: the epic's existing bugs and a text search on the symptom. If one exists, comment with the new evidence instead. If a closed bug is back, file a new one linked as "relates to" and call it a regression.

Each bug:
- **In the tracker's project,** **type** Bug, **parent** the epic, the run's **label**, plus `qa.security_label` if it touches who's signed in, sessions, account takeover, or data leaking between users or tenants. **Components** set, when `tracker.components_required`.
- **Summary:** what the user experiences, in plain words, not the internal cause.
- **Description:** what happened and what should have (cite the epic's flow table or story); numbered steps from a signed-out browser with exact URLs; environment (flags, branches, SHAs); evidence (screenshot, console errors, the failing request's method, path and status, with tokens and cookies removed); found by (scenario name, or "exploratory: charter N"); severity (blocks release / fix before release / can wait) with one sentence why.

Only file what you've reproduced by hand at least once.

**Give every behaviour bug a test that would catch it,** so the fix has something to automate and the bug can't quietly come back. Skip purely visual nits.
- **The covering test isn't marked automated yet:** add the bug's scenario to it (the tests adapter's "Update a test's scenarios", saving the current scenarios first).
- **The covering test is already marked automated:** don't add to it, which would make that false. Create a new test for the bug's scenario ("Create a test"), linked to the story, unmarked until it's automated.
- **No test covers it:** create one, the same way.

Link each test to its bug ("relates to"), and say in the bug which test it is. Whoever fixes the bug automates that test as part of the fix.

Problems with the test setup itself (for example "the e2e suite doesn't start") go in **one parent task with a subtask per problem**, when the user asks for them filed.

## 5. Report

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then start with the call: "Not ready: 2 release blockers (PROJ-X, PROJ-Y)." or "Ready, with 3 fix-soon bugs." Then:

1. Environment: flags, branches and SHAs.
2. e2e: passed, failed and skipped counts, with each failure in its bucket.
3. Exploratory: charters covered, and anything odd that wasn't a bug.
4. Tickets filed or commented on: key, summary, severity.

Report test results plainly: a test passed or it didn't.

## 6. Put the report on the epic

Post the same report as a comment on the epic, so the release decision sits next to the epic rather than in a chat. Start the comment with the date, the environment and the call. Don't change the epic's status or any story's status; that's the user's decision.
