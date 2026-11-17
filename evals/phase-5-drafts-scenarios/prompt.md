---
description: "With tests.kind repo-gherkin, shape-epic phase 5 creates tests as scenarios: comments on each story, full .feature text tagged with the story's key, a cross-cutting test on the last story it needs, and never files Xray tests."
tags: [shape-epic, issue-139]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys). You can't reach Jira or change files from here, so show me exactly what you'd post.

/shape-epic tests for epic PROJ-1260. Its two stories:

- PROJ-1261 "[Slice 1] Create an API key": a user names a key and creates it; it's listed with its name and creation date.
- PROJ-1262 "[Slice 2] Revoke an API key": a user revokes a key; it shows as revoked and calls with it get 401.

I've already approved this test plan, so create the tests:

- PROJ-1261: "A new key is listed with its name and creation date"
- PROJ-1262: "A revoked key shows as revoked", "A call with a revoked key gets 401"
- Cross-cutting: "Create a key, then revoke it" (needs both slices)
