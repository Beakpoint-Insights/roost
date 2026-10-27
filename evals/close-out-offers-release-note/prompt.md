---
description: After an epic's release ships, close-out-epic confirms production runs it using each repo's production key, then offers to draft the epic's release note rather than writing one unasked.
tags: [close-out-epic, release-notes, issue-60]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

PROJ-2400 has shipped. Finish the close-out. You can't reach Jira or GitHub from here, so here's what I found:

- release-please released acme-api 3.21.0 on March 3, 2026, and its release workflow run succeeded, including the Jira sync job.
- acme-api's `deploy-production.yml` succeeded on March 3 for the 3.21.0 tag.
- acme-web's last PR for the epic, acme/acme-web#461, merged into `main` on March 2. acme-web has no release; merging to `main` deploys it.
- Every ticket under PROJ-2400 is Done, except PROJ-2403, which is still Ready for Release; its fix is in acme-api 3.21.0.
- There are no person-owned tasks or manual tests in the epic.
