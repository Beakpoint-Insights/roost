---
description: At a retro's checkpoint, "ticket the check" on a hypothesis only the user can check files a person-owned task for the check, not a ticket for the change itself.
tags: [retro, issue-111]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

We're at the checkpoint of the retro on the PROJ-2789 slice. You can't reach Jira from here, so show me exactly what you'd file. This was the list:

| # | Severity | Finding | Recommendation | Where |
|---|---|---|---|---|
| 1 | High | `GET /api/usage` shipped with no page size; review passed it | Checked: add "list endpoints are paged" to acme-api's `review_focus` | Team config |
| 2 | Medium | `npm run seed -- --tenant qa` ran 5 times, ~100 minutes, same output each time | Hypothesis: start the stack from a database snapshot of the seeded tenant instead of seeding each time. Check: restore last month's snapshot from the shared backup bucket and confirm the usage totals match a fresh seed. Only you can run it: the bucket needs your cloud sign-in. About 15 minutes, against ~100 minutes per slice | acme-api |
| 3 | Low | 14 searches to find where the OpenAPI spec is built | Checked: point to `scripts/openapi/build.ts` in acme-api's `CLAUDE.md` | acme-api |

My decisions: 1 yes, 2 ticket the check, 3 skip.
