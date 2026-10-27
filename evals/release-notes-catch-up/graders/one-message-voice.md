---
type: llm
---

The example config's voice file (`examples/release-notes-voice.md`) asks for a sign-off on every note, rotated so none repeats within a batch.

It passes when both notes come together, complete, with nothing between them but the notes themselves (no commentary or questions between the two); the candidates and the checks or questions come after the notes; and the two notes end with different sign-offs.

It fails if commentary or questions sit between the two notes, if a note is missing its title or date, or if both notes use the same sign-off.
