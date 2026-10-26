---
description: With a GitHub-only config, verify-slice-tests treats a story's tests as eval cases tagged with its key, not Xray tests, and closes nothing.
tags: [verify-slice-tests, roost-config]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the GitHub-only example in the roost plugin, `examples/config.github-only.yml`.

Use verify-slice-tests for issue #42. You can't reach GitHub or run anything from here, so here's what I found:

- `evals/export-asks-first/` is committed on the branch. Its `prompt.md` tags are `[export, issue-42]`.
- #42 has an `evals:` comment with a second case, `export-names-the-format`, drafted in full. It isn't in `evals/` on the branch.

What's the state of #42's tests, and what happens next?
