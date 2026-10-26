---
type: llm
---

The reply is a short status report for PROJ-2788: a table with one row per step (backend kickoff, frontend kickoff, tests, code review, fixes, exploratory testing, slice done) and a state for each, followed by at most a line or two (such as what's next). This eval has no access to Jira or GitHub, so states shown as "unknown", with a one-line note that Jira and GitHub couldn't be read, are fine. It fails if the reply is mostly prose, offers to start or resume work, or invents states it couldn't have read.
