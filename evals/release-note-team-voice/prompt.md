---
description: With the team's own voice file in its config, a release note follows those rules (sentence-case titles, categories, sign-off, byline) instead of roost's fallback.
tags: [release-notes, issue-62]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, with its voice rules.

Draft the release note for PROJ-2400. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2400** (epic) "Know right away when spending jumps". Its only slice, PROJ-2401 "Email alerts when daily spend passes a threshold", is Done: PRs acme/acme-api#812 (merged February 27) and acme/acme-web#455 (merged March 2). Customers turn alerts on per project in Settings › Alerts, and the email arrives within 5 minutes of spend passing the threshold.
- acme-api's `deploy-production.yml` succeeded on February 28, and that run included #812. acme-web deploys on merge.
- None of our published notes mention it.
