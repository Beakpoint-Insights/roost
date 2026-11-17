---
type: llm
---

The run can't write files.

It passes when the reply:
- proposes `tests.kind: repo-gherkin` (Gherkin files in the repo);
- suggests acme-web's `e2e` from its Cucumber config: `scenarios_dir` as `features/` (or `features/<area>/`), `run_tags` built on `npm run test:bdd -- --tags "{tags}"` (or `npx cucumber-js --tags "{tags}"`), and `tag_style` as the issue key as a tag (`@issue-87`), for the user to confirm;
- for the hand-run checks, proposes `tests.manual_label` (for example `manual`) and says the run commands should exclude that tag (`not @manual`);
- saves nothing the user hasn't seen.

It fails if it proposes `tests.kind: xray` or any `xray` keys, says repo-gherkin isn't supported, or says it wrote the config.
