# Phase 6: Build Guide

**Input:** Slices (stories) + tests + the design (phase 3).

**Goal:** Create a visual artifact that serves as a developer handoff, showing what gets built in each slice, what the target state looks like after each slice (the UI, or where things run), and which tests should pass.

## Process

1. Gather all the pieces:
   - Epic description (from the tracker)
   - All stories/slices (from the tracker, ordered)
   - All the epic's tests (the tests adapter's "A story's tests", for each story), with their scenarios if helpful
   - The design: the prototype (for UI reference), the design doc (for where things run), or both

2. Build the guide as a single HTML artifact. Structure:

   **Header:** Epic title, key, and one-line summary.

   **Timeline Rail:** A vertical sequence of slice cards, one per slice, in build order. Each card shows:
   - Slice number, ticket key, and title
   - Brief description of what this slice adds
   - A picture of what changes in this slice, highlighting what's new:
     - **UI work:** UI mockup(s) of the screens it changes.
     - **Work with no UI:** a map of where things run, from the design doc: each environment or component, on the old platform or the new, with what this slice moves or adds highlighted.
     - **Both:** both pictures.
   - Test pills: which test issues should pass after this slice (with their keys)

   **Test Coverage Matrix:** A summary table at the bottom mapping every test to the slice where it first becomes passable. Cross-cutting tests show the last slice they depend on.

3. Design with the design system's colors (`design`), or the product's brand colors if there's none. Support light/dark themes.

4. Publish as a Claude artifact. **Then open the published page and check it yourself** before sharing the link: every slice card, picture, test pill and link, in light and dark, with no console errors (see "The signed-in browser" in `roost-config`). If you couldn't, say so first, and why.

5. Share the link, and tell the user it's private until they share it from the page.

## Design Guidance

- The guide is a communication tool for the developer. Optimize for scannability.
- UI mockups should be simplified representations, not pixel-perfect copies. Use CSS to approximate the prototype's key components. Maps of where things run use the same view of the system in every slice card, so the change from card to card is what stands out.
- Highlight what's NEW in each slice (use a "new" badge, outline, or color treatment)
- Make test pills clickable (link to the ticket)
- The guide should tell a story: "First we build X, which gives us Y, then we add Z..."

## Output

A published artifact URL that can be shared with the development team.
