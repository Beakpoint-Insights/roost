---
type: llm
---

Without `tests.manual_label`, there are no manual scenarios.

It passes when the reply proposes an automated scenario for the health page, tagged `@PROJ-1281`, and puts the curl check into PROJ-1281's acceptance criteria, to be checked with evidence, not into a scenario.

It fails if it writes a scenario tagged `@manual` (or any manual tag), writes a scenario for the curl check, or suggests adding `tests.manual_label` as the way to handle it without the user asking.
