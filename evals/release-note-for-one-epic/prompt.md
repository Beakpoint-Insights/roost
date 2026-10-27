---
description: A release note for one shipped epic is dated by its production deploy, not the tracker's resolution date, describes only what shipped, and leaves unknown facts blank.
tags: [release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2400. You can't reach Jira or GitHub from here, so here's everything I found:

- **PROJ-2400** (epic) "Know right away when spending jumps". Resolved March 17, 2026. Its plan: email alerts when daily spend passes a threshold, the same alerts in Slack, and a per-project threshold in Settings › Alerts. "Each plan includes a monthly allowance of alert emails."
- **PROJ-2401** [Slice 1] Email alerts when daily spend passes a threshold. Done. PRs: acme/acme-api#812 (merged February 27) and acme/acme-web#455 (merged March 2).
- **PROJ-2402** [Slice 2] Alerts in Slack. Won't Do: cut before it was built. No PRs.
- **PROJ-2403** [Slice 3] Set the threshold per project in Settings › Alerts. Done. PRs: acme/acme-api#820 (merged March 2) and acme/acme-web#461 (merged March 2).
- acme-api's `deploy-production.yml` succeeded on February 28 (it included #812) and on March 3 (it included #820). It didn't run in between.
- acme-web has no deploy workflow; merging to `main` deploys it.

Nothing says how many alert emails a plan includes.
