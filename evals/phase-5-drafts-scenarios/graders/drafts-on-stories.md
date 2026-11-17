---
type: llm
---

With `repo-gherkin`, phase 5 creates a test by drafting it on its story; the session that builds the story commits it first.

It passes when the reply:
- gives one comment for PROJ-1261 and one for PROJ-1262, each starting `scenarios:`;
- puts full Gherkin in each, in code blocks, as `.feature` text (a `Feature:` line and a `Background:` are allowed), tagged `@PROJ-1261` or `@PROJ-1262`;
- puts the cross-cutting "Create a key, then revoke it" on PROJ-1262, the last story it needs, tagged `@PROJ-1262`;
- says each story's building session commits the files first, under acme-web's `e2e.scenarios_dir`, test-first.

It fails if it files Jira Test issues, links tests with a "Test" link type, puts the cross-cutting test on PROJ-1261 or the epic, or writes only scenario titles without steps.
