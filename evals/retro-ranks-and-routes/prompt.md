---
description: A retro on one session turns the moments script's output into one ranked list, each finding with its evidence, what skipping it costs, a Checked or Hypothesis recommendation and where the fix goes; a mechanical mistake becomes a check, a review miss a review rule, an unproven speed-up a Hypothesis with its check, and nothing changes before the user decides.
tags: [retro, issue-111]
max_turns: 15
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Run a retro on the acme-api session from the PROJ-2789 slice. Its transcript isn't on this machine, but I already ran `retro_moments.py` on it; here's its output:

```json
{
  "session": "acme-api-3f",
  "window": ["2026-03-02T09:00:00Z", "2026-03-04T17:00:00Z"],
  "totals": {"turns": 212, "tool_calls": {"Bash": 140, "Read": 61, "Grep": 38, "Edit": 44}, "errors": 9},
  "moments": [
    {"kind": "correction", "time": "2026-03-02T11:14:00Z", "id": "r-0412",
     "excerpt": "user: we don't use moment in acme-api, it's date-fns everywhere. third time this week."},
    {"kind": "correction", "time": "2026-03-03T15:40:00Z", "id": "r-1290",
     "excerpt": "user: code review passed this but GET /api/usage returns every row for the tenant, no page size. that's 2M rows for big tenants."},
    {"kind": "slow", "command": "npm run seed -- --tenant qa", "repo": "acme-api",
     "runs": [{"time": "2026-03-02T09:05:00Z", "minutes": 19.4}, {"time": "2026-03-02T16:10:00Z", "minutes": 20.1},
              {"time": "2026-03-03T09:02:00Z", "minutes": 19.8}, {"time": "2026-03-03T14:30:00Z", "minutes": 21.0},
              {"time": "2026-03-04T09:01:00Z", "minutes": 20.3}],
     "count": 5, "total_minutes": 100.6,
     "excerpt": "Seeded tenant qa: 2,104,332 usage rows (same line after every run)"},
    {"kind": "search", "time": "2026-03-03T10:02:00Z", "id": "r-0877", "count": 14, "minutes": 6,
     "excerpt": "Grep/Read across acme-api looking for where the OpenAPI spec is generated; found scripts/openapi/build.ts"}
  ]
}
```
