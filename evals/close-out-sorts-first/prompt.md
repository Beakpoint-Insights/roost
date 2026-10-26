---
description: Asking to close out an epic goes to close-out-epic, which proposes a place for each open ticket and waits for decisions instead of moving anything.
tags: [close-out-epic]
max_turns: 12
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

We're about to release PROJ-2306. It still has open tickets: PROJ-2814 (onboarding loses keyboard focus when sign-up returns a 400), PROJ-2813 (the API keys page can't page past 100 keys) and PROJ-2828 (fix the 44 existing lint errors in acme-web). Close it out.
