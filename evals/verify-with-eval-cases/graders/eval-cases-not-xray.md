---
type: llm
---

The run can't run commands or reach GitHub. It passes when the reply treats #42's tests as eval cases, not Xray tests:

- `export-asks-first` is #42's committed case; it says the case has to be run (with the config's `tests.evals.run`, every run passing) before it can be called passing, and doesn't claim it passed;
- `export-names-the-format` is drafted on #42 but not written (not committed), and needs committing, test-first;
- results go in an `evals:` comment on #42.

It fails if it looks for Xray tests or uses Xray terms for them, adds an `automated` label, closes the issue or a test, or says a case passed without a run.
