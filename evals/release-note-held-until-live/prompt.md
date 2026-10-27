---
description: An epic with a slice not yet deployed and a correction to past data that hasn't run gets a held release note naming both things it waits for.
tags: [release-notes, issue-61]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2440. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2440** (epic) "Trust the costs you see". Its goal: costs were rounded down to the cent on every line, so totals were slightly low; fix the rounding for new costs, and recalculate past costs.
- **PROJ-2441** [Slice 1] Round costs correctly. Done. PR acme/acme-api#840, merged March 6.
- **PROJ-2442** [Slice 2] Recalculate past costs. Ready for Release. PR acme/acme-api#848, merged March 12. It adds a job someone runs by hand in production to recalculate costs from before the fix. Nobody has run it in production yet.
- acme-api's `deploy-production.yml` succeeded on March 6 (it included #840) and on March 10. It hasn't run since March 10.
