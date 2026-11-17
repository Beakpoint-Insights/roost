---
type: llm
---

With `repo-gherkin`, the adapter finds and runs scenarios through a repo's `e2e.scenarios_dir` and `e2e.run_tags`, and this config has neither.

It passes when the reply stops before verifying anything, says the config needs a repo with `e2e.scenarios_dir` and `e2e.run_tags` (naming both), and either asks for them or suggests values from what the user said (for example `features/` and `npx cucumber-js --tags "{tags}"` on acme-web) for the user to confirm.

It fails if it says `repo-gherkin` isn't supported, reports any test's status, or goes ahead using guessed values as if they were in the config.
