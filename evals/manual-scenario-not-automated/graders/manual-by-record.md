---
type: llm
---

With `repo-gherkin` and `tests.manual_label: manual`, a scenario tagged `@manual` is run by hand once and closed by a `manual run:` comment on the story.

It passes when the reply:
- reports `api-keys.feature` as automated and passing;
- reports `load-balancer.feature` as manual and not run yet (and that it's for after release), not "not automated"; says what has to be run (the curl check and what passing looks like) and that it closes on a passing `manual run:` comment on PROJ-1240;
- flags `dns.feature` as mixing a manual and an automated scenario, which a file mustn't, and proposes separating them.

It fails if it calls the load balancer check "not automated", proposes automating it or writing step definitions for it, proposes splitting `load-balancer.feature`, or adds an `automated` label or closes a ticket.
