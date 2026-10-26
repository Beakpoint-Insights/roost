# Slice Quality Checklist

Use this checklist when planning and reviewing slices (stories) under an epic.

## Per-Slice Checks

### Independence
- [ ] This slice can be merged and deployed without any later slice
- [ ] Everything works correctly after this slice ships (no broken UI, no dangling references, nothing half-built in an environment)
- [ ] No "phase 2" stub code that only makes sense after a later slice lands

### Verticality
- [ ] When it's done, something runs that you can observe and check
- [ ] For an epic with UI: includes all backend work needed for this slice's frontend to function, and all frontend work to expose this slice's backend capability, with no "backend-only" or "frontend-only" slices (unless the epic explicitly calls for one)
- [ ] For an epic with no UI: the slice leaves a running piece you can reach and check (an empty cluster you can reach, then staging running on it), not a layer that does nothing on its own

### Ordering
- [ ] Dependencies on earlier slices are explicit in the description
- [ ] No circular dependencies between slices
- [ ] The build order makes sense: infrastructure before features, error states before happy paths

### Scope
- [ ] The slice description says what's IN this slice (not just what the epic covers)
- [ ] Acceptance criteria are specific and testable
- [ ] UI changes reference specific components or views from the prototype; with no UI, what you can observe references the design doc's target state
- [ ] The `Repos:` line names every repo with work in the slice, and no other

### Testability
- [ ] At least one test scenario maps to this slice
- [ ] Test scenarios are written against observable behavior, not implementation
- [ ] Cross-cutting tests that partially depend on this slice are identified

## Ordering Heuristics

Default ordering when the dependency graph doesn't force a specific sequence:

1. **Fix what's broken** — Bug fixes, 500 errors, data integrity issues
2. **Infrastructure** — Schema changes, new endpoints, data pipeline plumbing
3. **Error states** — Empty states, loading states, timeout handling. Users will see these before the happy path works.
4. **Core signal** — The primary value-add. The thing the epic exists to deliver.
5. **Controls and refinement** — Time pickers, filters, progressive disclosure
6. **New surfaces** — New pages or views that depend on earlier work
7. **Cross-cutting polish** — Navigation flows, aggregate views, the "whole picture"

## Common Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| "Prepare the backend" or "lay the groundwork" slice | Ships nothing you can observe; hard to verify | Include something you can see and check: a UI element, or for work with no UI, a piece that runs and answers |
| "Wire up the frontend" slice | Assumes backend is stable; often blocked | Combine with the backend work |
| Mega-slice with 10+ acceptance criteria | Too large to review, too risky to merge | Split by surface or by user flow |
| Slice that only matters after a later slice | Violates independence; wasted effort if priorities shift | Reorder or merge into the dependent slice |
| Shared utility slice | "Add helper functions" isn't a feature | Fold utilities into the slices that use them |
