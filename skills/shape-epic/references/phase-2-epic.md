# Phase 2: Epic Definition

**Input:** Structured problem statement from Phase 1 (or equivalent context from the user).

**Goal:** Create an epic in the tracker with a rich, structured description.

## Process

1. Draft the epic summary (title). Keep it under 80 characters. It should name the capability, not the problem. Example: "Confidence That Things Are Working Correctly" (not "Fix missing health signals").

2. Build the epic description in the tracker's format (ADF for Jira; see the tracker adapter). The description should include all sections from the problem statement, formatted to read well in the tracker:
   - Use `h2` headings for major sections
   - Use tables for structured comparisons (before/after, in/out scope)
   - Use numbered lists for goals
   - Include the failure case study as a narrative block
   - Include technical context with specific table/API names

3. Set epic metadata:
   - **Project:** `tracker.jira.project`
   - **Type:** Epic
   - **Components,** when `tracker.components_required` is true: read the project's components ("List components" in the tracker adapter) and choose the ones that match what the epic touches, by each component's name and description. Propose them with why; the user decides. Set them at creation.
   - **Roadmap,** only if the config has `roadmap`: ask the user whether the epic goes on the product roadmap. The user decides; give your recommendation and why:
     - **Yes** for `roadmap.yes_when`.
     - **No** for `roadmap.no_when`.

     If it goes on the roadmap, follow the skill in `roadmap.skill` for what else to ask (such as a horizon and theme) and which labels or fields to set, recommending an answer for each. If it doesn't, add no roadmap labels.

4. Create the epic (see "Create" in the tracker adapter).

5. Present the created epic to the user with its key and a link.

## Output

An epic key (e.g., PROJ-1768) with a fully populated description.
