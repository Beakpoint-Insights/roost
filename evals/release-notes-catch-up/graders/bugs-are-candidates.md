---
type: llm
---

Standalone tickets aren't drafted unless the user picks them; they're listed as candidates.

It passes when PROJ-2501 (CSV export drops the last row) and PROJ-2510 (the Billing page typo) are listed as candidates the user can pick to include, each with a line saying what it is, and neither has a drafted note.

It fails if either bug gets a drafted note, or if either is missing from the reply.
