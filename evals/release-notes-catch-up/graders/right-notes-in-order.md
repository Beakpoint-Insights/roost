---
type: llm
---

Since February 1, 2026, customers got two epics: PROJ-2470 (pay by invoice), live February 20, and PROJ-2400 (spend alerts), live March 3. PROJ-2450 (invite by link) reached production on January 28, before the cut-off, although it was resolved on February 3.

It passes when the reply drafts exactly two epic notes, PROJ-2470's (February 20, 2026) first and PROJ-2400's (March 3, 2026) second, and leaves PROJ-2450 out, saying it reached production before February 1.

It fails if it drafts a note for PROJ-2450, if the notes are newest first, or if either note has a different date.
