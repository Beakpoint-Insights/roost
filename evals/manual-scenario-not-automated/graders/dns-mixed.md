---
type: llm
---

With `repo-gherkin` and `tests.manual_label: manual`, a scenario tagged `@manual` is run by hand once and closed by a `manual run:` comment on the story.

It passes when the reply flags `dns.feature` as mixing a manual and an automated scenario, which a file mustn't, and proposes separating them.
