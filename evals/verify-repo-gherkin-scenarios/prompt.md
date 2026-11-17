---
description: With tests.kind repo-gherkin, verify-slice-tests finds a story's scenarios by whole tag, sorts them by their run (passed, undefined, pending, failed), and records the result in a scenarios: comment with no label or status.
tags: [verify-slice-tests, roost-config, issue-138]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys). You can't reach Jira, change files or run anything from here.

Use verify-slice-tests for story PROJ-1250. Here's what I found on the branch, at commit `a1b2c3d`, in acme-web:

`e2e/features/keys/api-keys.feature`:

```gherkin
@PROJ-1250
Feature: API keys

  Scenario: A new key is listed with its name
    ...

  Scenario: A revoked key shows as revoked
    ...
```

`e2e/features/keys/key-rotation.feature`:

```gherkin
Feature: Key rotation

  @PROJ-1250
  Scenario: Rotating a key keeps its name
    ...

  @PROJ-12500
  Scenario: Rotation is audited
    ...
```

I ran `npm run test:e2e -- --tags "@PROJ-1250"` just now:

- A new key is listed with its name: passed
- A revoked key shows as revoked: undefined (step "the key is revoked" has no definition)
- Rotating a key keeps its name: failed (expected "prod-key", got "prod-key (2)")

Report PROJ-1250's tests and what happens next.
