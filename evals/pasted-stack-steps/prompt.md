---
description: GitHub's pasted stacked-PR conflict steps go to stacked-prs, and the reply doesn't ask for a go-ahead first.
tags: [stacked-prs, routing]
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Stacked pull requests rely on rebasing rather than merge commits to update your branch.

Use the gh stack CLI to resolve conflicts within your stack of branches.

Step 1 Checkout the stack of branches locally.
gh stack checkout 158
Step 2 Rebase the stack with changes from the base branch.
gh stack rebase
Step 3 Fix any conflicts and commit the result.
Step 4 Push the changes.
gh stack push
