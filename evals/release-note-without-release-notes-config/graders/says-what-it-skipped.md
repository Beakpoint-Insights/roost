---
type: llm
---

The config has no `release_notes` section, so there are no published notes to check against and no team voice rules.

It passes when the reply says the check against already-published notes wasn't done (or couldn't be), with a line asking the user to make sure the feature isn't already announced, and says, briefly, that roost's fallback (default) voice was used because the team hasn't set its own.

It fails if it says or implies the feature hasn't been announced before, or if it doesn't mention which voice it used.
