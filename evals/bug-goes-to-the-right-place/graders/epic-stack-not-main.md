---
type: llm
---

The run can't see other sessions, Jira or GitHub. The reply says the fix belongs on the PROJ-2306 epic's stack (a branch stacked on the epic's top branch, shipping with the epic), not a standalone PR from main, because the bug is part of an unreleased epic. It treats the work as done by the API session (it coordinates and doesn't write the code itself), and stops because it can't reach that session or read the ticket. It fails if it plans a branch from main or a standalone release, writes or offers to write the fix itself in this session, or asks for permission to start.
