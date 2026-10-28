---
description: Catching up since a date includes work marked done before the date that reached production after it, and leaves out what was live before it.
tags: [release-notes, issue-63]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, with its voice rules.

Catch us up on release notes since February 1, 2026. You can't reach Jira, GitHub or the web from here, so here's what I found.

Our published notes page's two newest posts are "Usage Reports by Email" (January 30, 2026) and "Faster dashboards" (January 12, 2026). Neither is about the tickets below.

I saved two runs of the search for tickets moved to Done or Ready for Release, with different start dates. Each returned 1 page; this is all of each. Use whichever the skill calls for.

**Since February 1, 2026:**

- **PROJ-2470** (epic) "Pay the way your finance team wants". Moved to Done February 20. Slice PROJ-2471, pay by invoice instead of card, from Settings › Billing: acme/acme-api#801 and acme/acme-web#440. acme-api's production run that included #801 succeeded February 20; acme-web#440 merged February 19.

**Since January 12, 2026:**

- **PROJ-2460** (epic) "Know who changed what". Moved to Ready for Release January 30. Slice PROJ-2461, an activity log in Settings › Activity: acme/acme-api#795 and acme/acme-web#436. acme-api's production run that included #795 succeeded January 31; acme-web#436 merged January 30.
- **PROJ-2465** (epic) "Invoices you can file". Moved to Ready for Release January 31. Slice PROJ-2466, download any invoice as a PDF from Settings › Billing: acme/acme-api#798 and acme/acme-web#438. acme-api's production run that included #798 succeeded February 3; acme-web#438 merged January 31.
- **PROJ-2470** (epic) "Pay the way your finance team wants". Moved to Done February 20. Slice PROJ-2471, pay by invoice instead of card, from Settings › Billing: acme/acme-api#801 and acme/acme-web#440. acme-api's production run that included #801 succeeded February 20; acme-web#440 merged February 19.

No diffs add feature flags, and no slices are waiting to deploy.
