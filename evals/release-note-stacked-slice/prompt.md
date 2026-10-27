---
description: "A slice merged into another slice's branch on a gh stack is dated by the commit that brought it onto main, not by its own merge, and a PR whose ticket key only contains the slice's key is left out."
tags: [release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2480. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2480** (epic) "Download costs as a spreadsheet". Resolved April 2, 2026.
- **PROJ-2481** [Slice 1] Export the cost table to CSV. Done. PRs: acme/acme-api#840 (merged into `main` March 10) and acme/acme-web#480 (branch `PROJ-2481-csv-export`, merged into `main` March 10).
- **PROJ-2482** [Slice 2] Choose which columns go in the export. Done. PRs: acme/acme-api#846 (merged into `main` March 12) and acme/acme-web#486 (branch `PROJ-2482-column-picker`).
- What `gh pr view` says about acme-web's PRs: #480 head `PROJ-2481-csv-export`, base `main`, merged March 10. #486 head `PROJ-2482-column-picker`, base `PROJ-2481-csv-export`, merged March 13, merge commit c4d2b80. #491 "Bring PROJ-2481-csv-export up to date", head `PROJ-2481-csv-export`, base `main`, squash-merged March 19, merge commit 5e7a9c1.
- Searching acme-web's merged PRs for "PROJ-2482" also returned acme/acme-web#495 "Fix rounding in the PROJ-24821 report", merged March 26.
- acme-api's `deploy-production.yml` succeeded on March 11 (it included #840) and March 13 (it included #846), and next on March 30.
- acme-web has no deploy workflow; merging to `main` deploys it.
