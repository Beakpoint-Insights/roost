# Phase 4: Slice Planning

**Input:** Epic with description + its design (phase 3): the prototype, the architecture or design-doc PR, or both.

**Goal:** Break the epic into ordered, independently-shippable vertical stories (slices).

## Process

1. Review the epic goals and the design: the prototype's surfaces, and the target state in the design doc. Identify the natural build order:
   - What's foundational? (error handling, data plumbing, infrastructure)
   - What adds visible value? (health signals, new UI, a new environment running)
   - What's additive? (new pages, advanced features)
   - What ties everything together? (cross-cutting views)

2. Draft the slice plan as an ordered list. Each slice should be:
   - **Vertical:** When it's done, something runs that you can observe and check. For UI work, that means the backend and frontend changes a user can see. For work with no UI, it means a running piece you can reach and check: an empty cluster you can reach, then staging running on it, then production on it. Never a layer that does nothing on its own
   - **Independently shippable:** After merging, the app works correctly (no half-states)
   - **Ordered by dependency:** Slice N can depend on Slice N-1 but not on Slice N+1

3. For each slice, define:

| Field | Content |
|-------|---------|
| **Title** | Short, specific (e.g., "Structured Error States") |
| **Scope** | What work is included, in each repo |
| **Repos** | The repos in `repos` with work in this slice, by `name`. Phase 7 names only these |
| **Acceptance Criteria** | Observable behaviors when done |
| **UI Changes** | Which prototype surfaces change in this slice. Leave it out when the epic has no prototype |
| **What you can observe** | For work with no UI: what's running after this slice and how to check it, from the design doc |
| **Dependencies** | Which earlier slices must be done first |

4. Present the slice plan. The user may reorder, split, merge, or add slices.

5. Create the stories in the tracker (see "Create" in the tracker adapter):
   - **Type:** Story
   - **Parent:** The epic key
   - **Summary:** "[Slice N] [Title]"
   - **Description:** Scope, a `Repos:` line, acceptance criteria, and the UI changes or what you can observe, in the tracker's format
   - **Labels:** Inherit epic labels where appropriate
   - **Components,** when `tracker.components_required` is true: the ones from the project's list ("List components" in the tracker adapter) that match what this story touches, usually its `Repos:` and the epic's Components. Show them in the slice plan (step 4) so the user approves them with it, and set them at creation

6. **Person-owned tasks.** Work the epic needs that no repo session can do (a PR to another company's repo, a video, a partner conversation, a launch post) isn't a slice. Propose each one with its owner and its "When" (before release, after release, or after a named slice), with your recommendation. Once the user agrees, create each as a Task under the epic, labelled `tracker.person_task_label` (default `person-owned`), assigned to its owner, with "When:" and "Done when:" lines at the top of its description. Work a repo in `repos` could do (a docs page in a docs repo, for example) is part of a slice instead.

7. Show the created stories and tasks with their keys.

## Slice Ordering Heuristics

These aren't rules, but they're good defaults:

1. **Infrastructure/plumbing first** — Schema changes, API endpoints, data pipeline work
2. **Error states early** — Empty states and error handling before happy-path features (users will see errors before features work)
3. **Core signal next** — The primary value-add of the epic
4. **Progressive enhancement** — Time controls, filtering, disclosure patterns
5. **New surfaces last** — New pages or views that depend on earlier signals
6. **Cross-cutting last** — Anything that spans multiple slices

## Output

Ordered stories under the epic, each with a clear scope and acceptance criteria.
