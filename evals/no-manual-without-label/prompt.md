---
description: With tests.kind repo-gherkin and no tests.manual_label, shape-epic phase 5 writes no manual scenarios; a one-off check goes into the story's acceptance criteria.
tags: [shape-epic, manual-tests, issue-140]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys) and without `tests.manual_label`. You can't reach Jira or change files from here.

/shape-epic tests for epic PROJ-1280, which moves our API behind a new load balancer. Its one story, PROJ-1281 "[Slice 1] API answers through the new load balancer", has two checks:

- The health page reports the new load balancer's name (our e2e suite can check this).
- After the DNS change, `curl -sI https://api.acme.example/health` from outside the VPN returns 200 with `x-served-by` naming the new load balancer. It's a one-off check against production.

Propose the tests for PROJ-1281.
