---
description: A progress update when nothing needs the user is a 🟢 heading and one plain line, nothing more.
tags: [run-slice, progress-updates]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

You're the orchestrator running run-slice for PROJ-2789 (epic PROJ-2306), and it's 13:50: time for the 5-minute progress update. Here's what you checked just now:

- API session: transcript active at 13:49; it's fixing 2 Copilot review threads on PR #603, and pushed one fix commit at 13:46.
- PR #603: checks 8 of 11 complete, all passing so far; mergeStateStatus BLOCKED while checks run; 2 open review threads.
- UI session: transcript active at 13:48, writing the create-dialog tests on `PROJ-2789-frontend`; 2 new commits since 13:40.
- Nothing is waiting on the user.


This run has no PushNotification tool and can't write files: skip the notification and the log line, and don't mention them.

Write the update.
