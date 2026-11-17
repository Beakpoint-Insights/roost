---
type: llm
---

The run can't reach Jira or Xray, so it says what it would change. With Xray, a split keeps the automated scenarios on the existing test and moves the rest to a new test.

It passes when the reply:
- keeps the two automated scenarios on PROJ-1251, saving its current scenarios to a local file first, then marks PROJ-1251 automated (the `automated` label, Done);
- creates a new Xray test for "The key's secret is emailed to its owner" with `create-xray-test`, linked to PROJ-1250, with the same Components, moved to Done without the `automated` label.

It fails if it deletes that scenario without creating a new test, moves it only into the story's acceptance criteria, or labels the new test automated.
