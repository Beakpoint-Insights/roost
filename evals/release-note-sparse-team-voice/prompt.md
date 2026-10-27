---
description: "A team voice file that sets only a few rules is still the whole voice: the note follows it and inherits none of roost's fallback rules, such as the fallback's title word limit."
tags: [release-notes, issue-62]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, except that its `release_notes.voice` points at our own voice file, `our-voice.md`, instead of Acme's. You can't read that file from here, so here's its whole text:

> **Titles:** sentence case, saying exactly what the customer gets. Use the title the product team asks for, word for word.
> **Body:** one short paragraph, no bullets.
> **End:** "Cheers, the Acme team" on its own line.

Draft the release note for PROJ-2400. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2400** (epic) "Know right away when spending jumps". Its only slice, PROJ-2401 "Email alerts when daily spend passes a threshold", is Done: PRs acme/acme-api#812 (merged February 27) and acme/acme-web#455 (merged March 2). Customers turn alerts on per project in Settings › Alerts.
- acme-api's `deploy-production.yml` succeeded on February 28, and that run included #812. acme-web deploys on merge.
- None of our published notes mention it.
- The product team asks for this title: "Email alerts when a project's daily spend passes your threshold".
