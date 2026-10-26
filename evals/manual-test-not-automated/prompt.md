---
description: verify-slice-tests reports a test labelled manual by its recorded runs, and never proposes automating or splitting it.
tags: [verify-slice-tests, manual-tests]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Use verify-slice-tests for story PROJ-1240. You can't reach Jira or Xray from here, so use what I've read for you:

- PROJ-1241 "API keys page lists every key": automated, labelled `automated`, Done. Its one scenario is in `e2e/features/keys/api-keys.feature`, tagged @PROJ-1241, and passed when I ran it just now.
- PROJ-1242 "The production load balancer answers on the new address": labelled `manual`, status To Do, no automation anywhere. Its description says: "Run `curl -sI https://api.acme.example/health` from outside the VPN after the DNS change. Passing: HTTP 200 and the `x-served-by` header names the new load balancer." It has no `manual run:` comment.

Report the table for PROJ-1240 and what happens next for each test.
