---
description: Catching up since a date drafts a note for each epic released since then, oldest first, drops what reached production before it, lists standalone bugs as candidates, and returns everything in one message.
tags: [release-notes, issue-63]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, with its voice rules.

Our last release notes post went out on February 1, 2026. Catch us up: everything released since then. You can't reach Jira, GitHub or the web from here, so here's what I found.

Tickets moved to Done or Ready for Release since February 1:

- **PROJ-2400** (epic) "Know right away when spending jumps". Slice PROJ-2401, email alerts when daily spend passes a threshold, set per project in Settings › Alerts: acme/acme-api#812 and acme/acme-web#455. acme-api's `deploy-production.yml` run that included #812 succeeded March 3; acme-web#455 merged March 2.
- **PROJ-2450** (epic) "Bring your team in without the admin". Slice PROJ-2451, invite teammates with a link: acme/acme-api#790 and acme/acme-web#430. Resolved February 3. acme-api's production run that included #790 succeeded January 28; acme-web#430 merged January 27.
- **PROJ-2470** (epic) "Pay the way your finance team wants". Slice PROJ-2471, pay by invoice instead of card, from Settings › Billing: acme/acme-api#801 and acme/acme-web#440. acme-api's production run that included #801 succeeded February 20; acme-web#440 merged February 19.
- **PROJ-2501** (bug) "CSV export drops the last row". acme/acme-api#805; its production run succeeded February 24. Customers saw it.
- **PROJ-2510** (bug) "Typo on the Billing page". acme/acme-web#445, merged February 12.

No diffs add feature flags, and no slices are waiting to deploy. Our published notes page's newest post is from January 30, 2026, "Usage Reports by Email", which isn't about any of these.
