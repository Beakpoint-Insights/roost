---
type: llm
---

The run can't change files or reach Jira, so it says what it would change.

It passes when the reply:
- keeps the two passing scenarios in `api-keys.feature`;
- deletes "The key's secret is emailed to its owner" from the file, in the story's PR;
- moves that check into PROJ-1250's acceptance criteria, to be checked on the PR with evidence;
- says the test is then automated once the remaining scenarios pass, recorded in the `scenarios:` comment.

It fails if it keeps the scenario in the suite under a tag the run excludes (`@wip`, `@skip`, `@ignore`), marks it manual, creates a new test ticket for it, or adds an `automated` label.
