---
description: Setting up release notes, setup recommends how each repo reaches production and asks for the team's voice rules (or offers to work them out from the published notes), saving nothing the user hasn't seen.
tags: [setup, issue-62]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`. You can't change files or reach GitHub from here.

Use roost's setup to get our config ready for release notes. What you need to know:

- acme-api goes to production through `.github/workflows/deploy-production.yml`, which runs on every release tag.
- acme-web is on Vercel: merging to `main` deploys it to production.
- Our published release notes are at https://acme.example/changelog. We've never written down how they should sound.
