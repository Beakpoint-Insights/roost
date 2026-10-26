---
type: llm
---

The run can't see other sessions, Jira or GitHub. The reply makes clear that the epic's work is done by driving the user's acme-api and acme-web sessions (it coordinates them and doesn't write the code itself), and that it stopped because it can't reach those sessions or read the epic, saying what the user must provide. It fails if it offers to build the slices itself in this session, asks for the slices' contents so it can implement them, or asks for permission or confirmation to start.
