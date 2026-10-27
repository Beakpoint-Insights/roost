---
description: "An epic that shipped two separate features gets one note for each, each dated by the last change that feature needed."
tags: [release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release notes for PROJ-2490. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2490** (epic) "Billing clean-up". Resolved March 27, 2026.
- **PROJ-2491** [Slice 1] Pay an invoice by bank transfer, from the invoice page. Done. PRs: acme/acme-api#870 (merged March 3) and acme/acme-web#510 (merged March 4).
- **PROJ-2492** [Slice 2] Download every invoice for a year as one ZIP file, from Billing › Invoices. Done. PR: acme/acme-web#522 (merged March 20).
- The two slices don't depend on each other: paying by bank transfer works without the ZIP download, and the other way round.
- acme-api's `deploy-production.yml` succeeded on March 5 (it included #870). acme-api has no changes for PROJ-2492.
- acme-web has no deploy workflow; merging to `main` deploys it.
