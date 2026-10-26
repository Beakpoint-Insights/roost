---
description: Asking to fix a bug goes to run-bug, which works out from the bug's parent whether the fix joins the epic's stack or gets its own PR from main, and doesn't edit code itself.
tags: [run-bug]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

PROJ-2822 is a bug under the PROJ-2306 epic, which hasn't been released yet. Ingest returns 500 for a span with no "attributes" field. Have the API agent fix it.
