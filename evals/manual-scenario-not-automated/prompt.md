---
description: "With tests.kind repo-gherkin, verify-slice-tests reports a scenario tagged manual by its manual run: comments, never as not automated, and flags a file that mixes manual and automated scenarios."
tags: [verify-slice-tests, manual-tests, issue-140]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys). Its `tests.manual_label` is `manual`. You can't reach Jira or run anything from here.

Use verify-slice-tests for story PROJ-1240. On the branch in acme-web:

`e2e/features/keys/api-keys.feature`, tagged `@PROJ-1240` on its `Feature:` line, with one scenario, "API keys page lists every key". It passed when I ran it just now.

`e2e/features/ops/load-balancer.feature`:

```gherkin
@PROJ-1240 @manual
Feature: Production load balancer

  Scenario: The production load balancer answers on the new address
    Run `curl -sI https://api.acme.example/health` from outside the VPN after the DNS change.
    Passing: HTTP 200 and the `x-served-by` header names the new load balancer.
    When: after release
```

`e2e/features/ops/dns.feature`, tagged `@PROJ-1240` on its `Feature:` line, has two scenarios: "DNS record points at the new load balancer", tagged `@manual`, and "Health check page renders", not tagged manual, which passed.

PROJ-1240 has no `manual run:` comment. Report the table and what happens next for each test.
