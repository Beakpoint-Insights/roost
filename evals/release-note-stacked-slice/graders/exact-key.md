---
type: llm
---

acme/acme-web#495 is for PROJ-24821, a different ticket whose key only contains PROJ-2482. It isn't part of PROJ-2480.

It passes when #495 isn't treated as one of the feature's changes: it doesn't date the note or appear in the evidence table as a change. Mentioning it in the checks as left out is fine.

It fails if the note is dated March 26, or the evidence table lists #495 as a change the feature needed.
