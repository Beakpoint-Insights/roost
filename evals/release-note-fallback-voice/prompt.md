---
description: "Without the team's own voice rules, a release note follows roost's fallback voice: a feature title, a category and date line, \"Previously… Now…\" for a fix, and no ticket keys, hype or sign-off."
tags: [release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but without `release_notes.voice`: we haven't set up our own voice rules yet.

Draft the release note for PROJ-2420. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2420** (epic) "Stop losing usage when uploads arrive late". Resolved March 12, 2026.
- **PROJ-2421** [Slice 1] Accept usage files up to 7 days late. Done. PR acme/acme-api#830, merged March 9. Before it, any usage file uploaded more than 24 hours after its period ended was rejected, and that usage never showed up on the customer's dashboard. Now files up to 7 days late are accepted, and their usage appears within 10 minutes of the upload. Customers don't need to change anything or re-upload.
- acme-api's `deploy-production.yml` succeeded on March 10, and that run included #830. There were no acme-web changes.
