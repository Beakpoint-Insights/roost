---
description: With tests.kind repo-gherkin and no repo that has e2e.scenarios_dir and e2e.run_tags, roost-config stops and names the missing keys, instead of saying repo-gherkin isn't supported or guessing them.
tags: [roost-config, verify-slice-tests, issue-138]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys), and with no `e2e` section on any repo. Our scenarios are in `features/` in acme-web and we run them with `npx cucumber-js`. You can't change files from here.

Use verify-slice-tests for story PROJ-1250.
