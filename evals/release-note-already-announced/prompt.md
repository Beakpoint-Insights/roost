---
description: A feature the team's published release notes already announce isn't announced again; the draft is dropped or flagged, naming the published post.
tags: [release-notes, issue-61]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2400. You can't reach Jira, GitHub or the web from here, so here's what I found:

- **PROJ-2400** (epic) "Know right away when spending jumps". Its only slice, PROJ-2401 "Email alerts when daily spend passes a threshold", is Done: PRs acme/acme-api#812 (merged February 27) and acme/acme-web#455 (merged March 2).
- acme-api's `deploy-production.yml` succeeded on February 28, and that run included #812. acme-web deploys on merge.

I fetched our published release notes page (the `release_notes.published_url` in our config). Its newest posts:

> **Spend Alerts by Email**
> New · March 4, 2026
> You can now get an email the moment a project's daily spend passes a threshold you set. Turn it on in Settings › Alerts.
>
> **Faster Dashboard Loading**
> Improvement · February 18, 2026
> Dashboards now load in under a second, even for accounts with years of history.
