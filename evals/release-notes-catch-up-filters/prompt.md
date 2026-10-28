---
description: Catching up from a Jira search keeps only tickets still done or ready for release, drops Tests and sub-tasks, and says the search was read to its last page.
tags: [release-notes, issue-63]
max_turns: 20
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, with its voice rules.

Catch us up on release notes since February 1, 2026. You can't reach Jira, GitHub or the web from here, so here's what I found.

I ran the search for tickets moved to Done or Ready for Release since February 1. It returned 2 pages; this is all of both:

- **PROJ-2470** (epic) "Pay the way your finance team wants". Now Done. Slice PROJ-2471, pay by invoice instead of card, from Settings › Billing: acme/acme-api#801 and acme/acme-web#440. acme-api's production run that included #801 succeeded February 20; acme-web#440 merged February 19.
- **PROJ-2472** (sub-task of PROJ-2471) "Add the invoice option to the billing form". Now Done. acme/acme-web#440.
- **PROJ-2475** (Test) "Pay by invoice from Settings › Billing". Now Done.
- **PROJ-2520** (bug) "Usage chart shows the wrong month". Moved to Done on February 10, then back to To Do on February 12. acme/acme-web#450, merged February 9, was reverted by acme/acme-web#452 on February 12.

No diffs add feature flags. Our published notes page's newest post is from January 30, 2026, "Usage Reports by Email".
