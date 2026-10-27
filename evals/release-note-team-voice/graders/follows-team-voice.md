---
type: llm
---

The example config's `release_notes.voice` names Acme's voice file, `examples/release-notes-voice.md`, which replaces roost's fallback voice. Its rules include: titles in sentence case (only the first word and names capitalised); the categories New, Better and Fixed; a sign-off on every note, taken from its list; and its byline at the end.

It passes when the note's title is in sentence case, its category is one of New, Better or Fixed, and it ends with a sign-off from the voice file's list and the voice file's byline.

It fails if the title is in Title Case (the fallback's rule), the category is "Improvement" or "Fix", or the note has no sign-off or no byline.

If the reply shows the voice file couldn't be read, it fails.
