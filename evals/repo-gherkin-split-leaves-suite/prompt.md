---
description: With tests.kind repo-gherkin, an agreed split removes the scenarios that won't be automated from the file and moves each one's check into the story's acceptance criteria, instead of parking them under a skip tag.
tags: [verify-slice-tests, issue-138]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys). You can't reach Jira or change files from here.

We're using verify-slice-tests for story PROJ-1250. Its test `e2e/features/keys/api-keys.feature` has three scenarios tagged @PROJ-1250. Two pass. The third, "The key's secret is emailed to its owner", is undefined: nothing in our e2e suite can read email, and we've agreed it won't be automated. You proposed splitting it, and I agree: go ahead with the split.

Say exactly what changes, in the repo and on PROJ-1250.
