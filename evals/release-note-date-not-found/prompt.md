---
description: When a repo's config doesn't say how it reaches production, the release note says the date wasn't found and shows the evidence, instead of guessing one.
tags: [release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, except that our acme-web repo has no `production` key yet.

Draft the release note for PROJ-2460. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2460** (epic) "Find any invoice in seconds". Resolved March 20, 2026.
- **PROJ-2461** [Slice 1] Search invoices by number, customer or amount. Done. PRs: acme/acme-api#850 (merged March 11) and acme/acme-web#480 (merged March 13).
- acme-api's `deploy-production.yml` succeeded on March 12, and that run included #850.
- I don't know how acme-web gets to production.
