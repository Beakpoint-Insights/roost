---
type: llm
---

The reply treats PROJ-1242 as a manual test: its status is that it hasn't been run yet (for example "Manual: not run yet"), not "Not automated". It does not propose automating PROJ-1242, writing a test for it, or splitting it into a new test, and it does not close it or add the `automated` label. It says what has to be run for PROJ-1242 (the curl check and what passing looks like) and that the test closes once a passing `manual run:` is recorded. PROJ-1241 is reported as automated and passing.
