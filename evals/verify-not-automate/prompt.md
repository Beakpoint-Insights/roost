---
description: Checking which tests are automated after a push goes to verify-slice-tests, not automate-xray-tests.
tags: [verify-slice-tests, routing]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

I've pushed everything for story PROJ-1235. Tell me which of its Xray tests are automated and passing, and close the ones that are. Don't write any new tests.
