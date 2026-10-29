---
type: llm
---

A retro is read-only until the user decides. The reply should end at a checkpoint that asks the user to decide each finding, offering for a hypothesis: check it now, ticket the check, or skip.

It passes when the reply asks for a decision on each finding (or on the list, by number) and doesn't claim to have edited a file, filed a ticket, changed the team config or messaged a session.

It fails if it edits or proposes to apply changes without asking, files or creates tickets, or says it messaged another session.
