---
description: With tests.kind repo-gherkin, live-verified-bdd files approved scenarios as a .feature file on the current branch in the repo that holds them, tagged with the story's key, not through create-xray-test.
tags: [live-verified-bdd, issue-139]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`, but with `tests.kind: repo-gherkin` (and no `xray` keys). This session is in acme-web, on branch `PROJ-1270-key-labels-frontend`. You can't change files from here, so say exactly what you'd write and where.

We used live-verified-bdd for story PROJ-1270 and walked these scenarios in the app. I approve them; file them:

```gherkin
Scenario: A key's label is shown next to its name
  Given I am signed in as an admin
  And a key named "prod-key" with the label "billing"
  When I open the API keys page
  Then "prod-key" shows the label "billing"

Scenario: A key with no label shows none
  Given I am signed in as an admin
  And a key named "test-key" with no label
  When I open the API keys page
  Then "test-key" shows no label
```
