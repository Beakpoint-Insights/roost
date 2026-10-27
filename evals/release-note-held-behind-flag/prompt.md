---
description: A feature that shipped behind a feature flag gets a release note that's drafted but held, waiting on the flag's rollout, with no date yet.
tags: [release-notes, issue-61]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Draft the release note for PROJ-2430. You can't reach Jira or GitHub from here, so here's what I found:

- **PROJ-2430** (epic) "See which teams drive spend". Resolved March 9, 2026.
- **PROJ-2431** [Slice 1] A Spend by Team page. Done. PRs: acme/acme-api#835 (merged March 4) and acme/acme-web#470 (merged March 5).
- acme-api's `deploy-production.yml` succeeded on March 5, and that run included #835.
- acme-web#470's diff adds the page's link to the side navigation:

```tsx
+  {flags.isEnabled("spend-by-team") && (
+    <NavLink to="/spend/teams">Spend by team</NavLink>
+  )}
```
