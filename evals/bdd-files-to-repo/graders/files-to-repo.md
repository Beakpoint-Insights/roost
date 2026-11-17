---
type: llm
---

With `repo-gherkin`, in the repo that holds the scenarios, filing means writing the `.feature` file on the current branch.

It passes when the reply writes (or says it would write) one `.feature` file under acme-web's `e2e/features/<area>/` (for example `e2e/features/keys/`), on branch `PROJ-1270-key-labels-frontend`, holding both scenarios, tagged `@PROJ-1270` on the `Feature:` line or on each scenario.

It fails if it creates a Jira Test issue, posts the scenarios only as a comment on PROJ-1270 instead of writing the file, uses a different branch, or tags them with anything other than PROJ-1270's key.
