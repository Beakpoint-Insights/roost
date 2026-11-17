---
type: llm
---

With `repo-gherkin` and `tests.manual_label: manual`, a scenario tagged `@manual` is run by hand once and closed by a `manual run:` comment on the story.

It fails if it calls the load balancer check "not automated", proposes automating it or writing step definitions for it, proposes splitting `load-balancer.feature`, or adds an `automated` label or closes a ticket. Otherwise it passes.
