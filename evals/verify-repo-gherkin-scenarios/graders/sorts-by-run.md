---
type: llm
---

The run can't reach Jira or run anything. With `repo-gherkin`, a story's tests are the `.feature` files with scenarios carrying its tag, found by the whole tag; each file is one test.

It passes when the reply:
- reports two tests for PROJ-1250, `api-keys.feature` and `key-rotation.feature`;
- leaves "Rotation is audited" out, because its tag is `@PROJ-12500`, not `@PROJ-1250`;
- reports "A new key is listed with its name" as automated and passing, "A revoked key shows as revoked" as not automated (an undefined step), and "Rotating a key keeps its name" as failing;
- says neither test is automated, since each has a scenario that didn't pass;
- says the result goes in a `scenarios:` comment on PROJ-1250, with each scenario's result and commit `a1b2c3d`, and sets no label or status.

A table, and next steps (write the missing step definition, look at the failure, or a split proposal under verify-slice-tests step 7, with automating the rest offered), are fine.

It fails if it counts "Rotation is audited" as PROJ-1250's, calls the undefined scenario failing or the failed one not automated, looks for Xray Test issues, adds an `automated` label, or moves any ticket to Done.
