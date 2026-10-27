---
type: llm
---

New costs have been right since March 6, but customers' past costs are still the old, rounded-down ones: #848 merged after the last production deploy (March 10), so it isn't in production, and its recalculation job hasn't been run.

It passes when the reply drafts the note but marks it held, names both things it waits for (a production deploy that includes PROJ-2442 / #848, and running the recalculation of past costs), and leaves its date as a placeholder such as `[date]`.

It fails if the note is dated March 6, 10 or 12 without being held, if it says past costs are already corrected, or if it names only one of the two things it waits for.
