---
description: With no release_notes section in the config, the skill says the repeat check wasn't done and that roost's fallback voice was used, and dates the note from the repo's release.
tags: [release-notes, issue-62]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the GitHub-only example in the roost plugin, `examples/config.github-only.yml`.

Draft the release note for #42. You can't reach GitHub from here, so here's what I found:

- **#42** (epic) "Get answers out of the assistant and into a file". Its only story, #43 "Export a conversation as Markdown", is closed as completed, by PR acme/acme-skills#90, merged March 6, 2026.
- acme/acme-skills published release v1.4.0 on March 8, 2026, the first release that includes #90.
