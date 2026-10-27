---
type: llm
---

The example config's `release_notes.voice` names Acme's voice file, which is the team's whole voice: when it's read, none of roost's fallback voice applies, and nothing is added from it.

It passes when the note follows only Acme's rules (a sentence-case title; New, Better or Fixed; a sign-off from its list; its byline), and the reply doesn't say it used, mixed in or fell back to roost's fallback or default voice.

It fails if the title is in Title Case, the category is Improvement or Fix, the note has no sign-off or byline (the fallback has none), or the reply says any fallback or default voice rule was used alongside the team's.
