---
type: llm
---

Only PROJ-2470 is released work customers can use: PROJ-2472 is a sub-task (its work is part of PROJ-2470), PROJ-2475 is a Test, and PROJ-2520 is back in To Do, its fix reverted.

It passes when the reply drafts exactly one note, PROJ-2470's, dated February 20, 2026; doesn't draft or list PROJ-2472 or PROJ-2475 as notes or candidates; and doesn't draft PROJ-2520 or offer it as a candidate, saying in the checks that it moved back to To Do.

It fails if PROJ-2472, PROJ-2475 or PROJ-2520 gets a note or is offered as a candidate, or if PROJ-2520 isn't mentioned at all.
