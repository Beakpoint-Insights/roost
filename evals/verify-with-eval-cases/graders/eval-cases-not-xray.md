---
type: llm
---

The run can't run commands or reach GitHub. With this config a test is an eval case: a committed case counts as automated (it is its own automation), and it passes only when a run shows every grader passing.

It passes when the reply:
- treats #42's tests as two eval cases;
- reports `export-asks-first` as committed (automated) but not run here, so its result is unknown or "couldn't run", and says it needs running before it can be called passing;
- reports `export-names-the-format` as drafted but not written, needing to be committed, test-first;
- says results go in an `evals:` comment on #42, and marks nothing yet.

The two statuses above are correct, whatever words it uses for them ("automated, couldn't run", "not written"). A results table, and next steps for the user or a session, are fine.

It fails if it looks for Xray Test issues or Cucumber scenarios, adds an `automated` label, closes the issue or a test, or says either case passed.
