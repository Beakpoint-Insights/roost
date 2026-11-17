---
type: llm
---

With `repo-gherkin` and `tests.manual_label: manual`, a scenario tagged `@manual` is run by hand once and closed by a `manual run:` comment on the story.

It passes when the reply reports `load-balancer.feature` as manual and not run yet (and that it's for after release), not "not automated"; says what has to be run (the curl check and what passing looks like) and that it closes on a passing `manual run:` comment on PROJ-1240.
