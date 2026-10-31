---
type: llm
---

Two findings say where a fix belongs. The banned `moment` import, corrected repeatedly, is a mechanical rule: the recommendation should be a deterministic check in acme-api (a lint rule such as ESLint's `no-restricted-imports`, a hook or a CI job). The unpaged list endpoint is something review should have caught: the recommendation should be a review rule (acme-api's `review_focus` in the team config, or its coding standards), so it binds the reviewer.

It passes when the `moment` finding recommends a lint rule, hook or CI check, and the paging finding recommends a review rule or coding standard.

It fails if either is recommended only as a new line in `CLAUDE.md` or `AGENTS.md`, or if the reply proposes fixing the code itself as the finding's destination.
