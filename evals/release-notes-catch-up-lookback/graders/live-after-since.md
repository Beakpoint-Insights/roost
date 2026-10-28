---
type: llm
---

Customers got two epics on or after February 1, 2026: PROJ-2465 (invoice PDFs), live February 3, though it was marked Ready for Release on January 31; and PROJ-2470 (pay by invoice), live February 20. PROJ-2460 (the activity log) was live January 31, before February 1.

It passes when the reply drafts exactly two epic notes, PROJ-2465's (February 3, 2026) first and PROJ-2470's (February 20, 2026) second, and leaves PROJ-2460 out, saying it reached production before February 1.

It fails if PROJ-2465 is left out (for example because it was marked done before February 1), if it drafts a note for PROJ-2460, if the notes are newest first, or if either note has a different date.
