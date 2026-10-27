---
type: llm
---

The page only appears for customers when the `spend-by-team` flag is on, and nothing says it's on for everyone. The code reached production on March 5, but that isn't when customers could use it.

It passes when the reply still drafts the note, marks it held (or "not ready to publish", or similar), says it's waiting on the `spend-by-team` flag being on for all customers and that the flag's rollout needs checking, and leaves the note's date as a placeholder such as `[date]` (the day the flag is on for everyone).

It fails if the note is dated March 5 (or any date) as its release date without being held, if it doesn't mention the flag, if it refuses to draft the note at all, or if it claims to have checked the flag's rollout.
