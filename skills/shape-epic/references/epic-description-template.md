# Epic Description Template

This is the recommended structure for a product epic description. It has proved effective as a developer communication tool.

## Sections

### Summary

One paragraph. What this epic delivers and why it matters. Name the user and the problem.

### Problem Statement

2-3 paragraphs. Frame the gap between what users need and what the system currently provides.

If applicable, use Don Norman's "gulf of evaluation" concept: the user takes an action but can't tell if the system responded correctly. What information is missing? What feedback loop is broken?

### Goals

Numbered list, 3-5 items. Each goal should be:
- Observable (someone can watch a user and confirm it)
- Specific (names the surface, signal, or behavior)
- Independent (achieving goal 3 doesn't require goal 2)

Example:
1. A user can confirm data is arriving within 30 seconds of opening the dashboard
2. A user can distinguish between "no data" and "data delayed" without checking logs
3. A user can identify which cost-calculation tags are missing coverage

### Real-World Failure Case Study

A specific incident (real or realistic) that illustrates the problem. Include:
- **Date** (real or approximate)
- **What happened** (the sequence of events)
- **What the user experienced** (what they saw, what they couldn't see)
- **What should have happened** (the target experience)
- **Root cause** (what the system lacked)

This grounds the epic in concrete reality. Abstract problem statements produce abstract solutions.

### DOET Audit (Optional)

If the epic improves an existing UI, score it against Norman's Design of Everyday Things principles:

| Principle | Current Score | Target Score | Gap |
|-----------|--------------|--------------|-----|
| Visibility | 3/10 | 8/10 | No health signals on dashboard |
| Feedback | 4/10 | 9/10 | Errors shown but not actionable |
| Mapping | 6/10 | 8/10 | Time picker doesn't show data boundaries |
| Constraints | 5/10 | 8/10 | Can select time ranges with no data |
| Affordance | 7/10 | 8/10 | Buttons clear but states ambiguous |

### Technical Context

What a developer needs to know about the system to build this. Include:
- Relevant tables, views, and their characteristics (row counts, retention, query patterns)
- API endpoints involved
- Data flow (where does the data come from, how does it move, where does it land)
- Performance constraints (query timeouts, data volumes, latency budgets)
- Existing technical debt that affects this work

Use specific names: `vw_traces_grid`, `cost_calculation_work_items`, not "the traces view" or "the cost table."

### Scope

Two columns: **In Scope** and **Out of Scope**. Be explicit about boundaries, especially:
- What this epic does NOT do (even if it seems related)
- What's deferred to a follow-up epic
- What's someone else's problem

### Success Metrics

How you'll know the epic succeeded, measured after shipping:

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Time to confirm ingestion health | >5 min (check logs) | <30 sec (glance at dashboard) | User testing |
| Support tickets re: "is data arriving?" | ~3/week | 0 | Support queue |
| Mean time to diagnose missing coverage | Unknown | <2 min | Incident review |

Prefer behavioral metrics over system metrics. "User can answer X in Y seconds" beats "API responds in Z ms."
