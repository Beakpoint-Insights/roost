---
description: "When a published post announced only an early beta of part of a feature, the finished feature still gets a new note, about what's new since that post, naming the post."
tags: [release-notes, issue-61]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2450. You can't reach Jira, GitHub or the web from here, so here's what I found:

- **PROJ-2450** (epic) "Know right away when spending jumps". Resolved April 8, 2026.
- **PROJ-2451** [Slice 1] Email alerts when an account's daily spend passes a threshold. Done. PR acme/acme-api#880, merged March 18.
- **PROJ-2452** [Slice 2] Set a different threshold for each project, in Settings › Alerts. Done. PRs acme/acme-api#891 (merged April 1) and acme/acme-web#530 (merged April 2).
- acme-api's `deploy-production.yml` succeeded on March 19 (it included #880) and on April 3 (it included #891).
- acme-web deploys on merge.
- acme-web#530 also removed the `spend-alerts-beta` flag check, so alerts are on for every account.

I fetched our published release notes page (the `release_notes.published_url` in our config). Its newest posts:

> **Spend Alerts by Email (Beta)**
> New · March 20, 2026
> Accounts in our beta program can now get an email when their daily spend passes a threshold. One threshold per account for now.
>
> **Faster Dashboard Loading**
> Improvement · February 18, 2026
> Dashboards now load in under a second, even for accounts with years of history.
