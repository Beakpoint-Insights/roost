---
description: With Xray, an agreed split still keeps the automated scenarios on the existing test and puts the rest on a new test created with create-xray-test, unlabelled, instead of deleting them.
tags: [verify-slice-tests, issue-138]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`. You can't reach Jira or Xray from here, so say exactly what you'd change.

We're using verify-slice-tests for story PROJ-1250. Its test PROJ-1251 "API keys" has three scenarios. Two are automated in `e2e/features/keys/api-keys.feature` and passed just now. The third, "The key's secret is emailed to its owner", has no automation: nothing in our e2e suite can read email, and we've agreed it won't be automated. You proposed splitting it, and I agree: go ahead with the split.
