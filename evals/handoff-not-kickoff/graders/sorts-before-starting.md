---
type: llm
---

The reply works on closing out the finished story before the next one starts. It gathers or asks about the open items the prompt mentions (the deferred bugs and the reopened test), proposes where each goes (the next slice, before release, or later), and mentions checking the epic's tests or updating the next story's kickoff. This eval has no access to Jira or GitHub, so saying it couldn't read them is fine. It fails if it starts the next story, offers to start it, or says it sent the next story's kickoff to a session, at any point: getting ready doesn't include kicking off. Asking a session to run the epic's existing tests is part of the handoff and is fine.
