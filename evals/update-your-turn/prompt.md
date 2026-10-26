---
description: A progress update while a session is blocked on the user leads with a YOUR TURN block whose actions come first.
tags: [run-slice, progress-updates]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

You're the orchestrator running run-slice for PROJ-2789 (epic PROJ-2306), and it's 13:45: time for the 5-minute progress update. Here's what you checked just now:

- API session: its transcript was last active at 13:31. Its last message says it's blocked: "The AWS SSO session expired. The user needs to run aws sso login --profile acme-dev in this terminal before I can run the pricing import tests."
- UI session: idle since 13:20, waiting for the API session's endpoint, as planned.
- PR #603 (backend): last commit at 13:29, checks 11 of 11 passed, mergeStateStatus CLEAN, no open review threads.
- No PR for the frontend yet.


This run has no PushNotification tool and can't write files: skip the notification and the log line, and don't mention them.

Write the update.
