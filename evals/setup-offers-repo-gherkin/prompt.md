---
description: For a team with .feature files and no test-management tool, setup offers Gherkin files in the repo, suggests each repo's e2e keys from its Cucumber config for the user to confirm, and writes no Xray keys.
tags: [setup, issue-141]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Set up roost for our team. You can't change files or reach GitHub from here. We've already settled the tracker (GitHub Issues in `acme/acme-web`) and repos (just `acme/acme-web`), so start at tests. What you need to know:

- We don't use Xray or any test-management tool. Our Cucumber scenarios are `.feature` files in the repo.
- acme-web's `cucumber.js`:

  ```js
  module.exports = { default: { paths: ['features/**/*.feature'], require: ['features/steps/**/*.ts'] } };
  ```

- `package.json` has `"test:bdd": "cucumber-js"`.
- Our scenarios are tagged with their issue, like `@issue-87`.
- Some checks we run by hand once against production, and we'd like to track those too.
