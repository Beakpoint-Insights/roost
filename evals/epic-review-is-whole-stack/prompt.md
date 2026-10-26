---
description: Asking whether an epic has been reviewed goes to review-epic, which works out what was and wasn't reviewed and asks the sessions for a whole-stack review against main, instead of reviewing code itself.
tags: [review-epic]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

We're close to releasing PROJ-2306. Each slice got a code review, but I don't think the bug-fix PRs did, and nobody has looked at the whole thing together. Has this epic been reviewed properly? Sort it out before we release.
