# Phase 3: Design

**Input:** Epic description with goals, scope, and technical context.

**Goal:** Show the target state after all work is complete, in the artifact that fits the work: a **UI prototype** for what users will see, an **architecture or design-doc PR** for how the system is built or run (infrastructure, services, data flows, a move between platforms), or **both** when the epic changes both.

## Choose the artifacts

Read the epic description and decide which artifacts it needs, then propose them to the user with your recommendation and why:

- **A UI prototype** if any page, panel, widget or state a user sees changes. Follow "UI prototype" below.
- **An architecture or design doc** if the epic changes how the system is built, deployed or connected: new infrastructure, a new service, a new data flow, a move from one platform to another, or a decision a later reader will ask "why?" about. Follow "Architecture or design doc" below.
- **Both,** when the epic does both. Build the architecture first if the UI depends on its decisions, otherwise in either order.

An epic with no UI change has no prototype, and later phases leave out everything that's about one. For such an epic the artifact isn't a question with options: say it will be an architecture or design-doc PR, and why, without listing a prototype as a choice. Questions about the doc itself (where it goes, the decisions it records) still come with options and your recommendation.

## UI prototype

1. Read the epic description carefully. Identify every surface (page, panel, widget, state) that needs to change.

2. **Find how the app already does the same job.** Before designing anything, look for existing screens that do something similar (another integration, another settings page, another list or wizard): in the code of the repos in `repos`, and in the design system's patterns. Read how they're built: the flow, the components, what's shared between them, and what deliberately doesn't exist (for example, no per-vendor detail page). Name them to the user. The prototype follows those patterns; a new screen or flow that breaks one is a decision for the user, with your recommendation.

3. List the UI surfaces, each with the existing screen it follows, and present them to the user:

```
Based on the epic, I'd prototype these surfaces:
1. Dashboard — health strip with 3 cells (ingestion, priceable, attribution)
2. Dashboard — error/empty states for each panel
3. Traces page — time picker with CA boundary indicator
4. Coverage page — new page with coverage bars by tag group
5. Cost Scout — unpriceable span teaser

Does this look right? Anything to add or cut?
```

4. **Load the design system first.** It's `design.system`, at `design.url`. Read it with `design.read_with`, starting with `design.read_first`. **If you can't reach it, stop and tell the user.** Don't fall back to guessing the look from the app's code or screenshots. The design systems in `design.not_ours` aren't this team's, even when they're in the same account. If the config has no `design`, ask the user what the prototype should follow before building it.

5. Build the prototype as a single, self-contained HTML file:
   - Use the design system's tokens, component classes and patterns, including its dark mode
   - Bundle everything inline (CSS, JS, no external dependencies)
   - Make it interactive: clickable navigation between views, state toggles, demo controls
   - Include a "tweak panel" or state controls so the user can see different states (healthy, warning, error, empty)
   - Show realistic data, not lorem ipsum
   - Keep the file under 5MB

6. Save the prototype to `<team.drafts_dir>/[Epic Summary] (standalone).html`

7. **Click through it yourself before showing it:** every view, state and control, with no console errors (see "The signed-in browser" in `roost-config`; a local file doesn't need the signed-in one). If you couldn't, say so first, and why.

8. Ask the user to open it in a browser and review. Iterate on feedback.

### Prototype guidance

- Match the design system's visual language (component classes, color tokens, spacing). Where the app and the design system differ, the design system wins.
- When one prototype covers screens from several epics, label each screen or step with the epic that builds it, and give the controls bar a toggle to hide the labels.
- Every interactive state the slices will build should be demonstrable in the prototype
- The prototype is a communication tool, not production code. Favor clarity over engineering.
- Include all target-state views, even if some won't be built until later slices

## Architecture or design doc

1. **Find where the team keeps design decisions,** and how: an architecture repo, a `docs/` folder in one of the `repos`, a wiki. Look for existing ADRs and diagrams (C4 views, deployment diagrams) and follow their format and tools. If you can't find a home, ask the user, recommending one.

2. **Read the current system first.** The code in the repos the epic touches, and what's actually running (read-only, as phase 1 describes). The doc describes a change from what is, so get what is right.

3. **Write the decisions down,** one ADR (or the format the team uses) per decision that a later reader would question: what was chosen, the options considered, and why. Settle them with the user as you go; each is a decision for them, with your recommendation.

4. **Draw the target state:** diagrams of what runs where after the epic (deployment and container views, for example), in the team's diagram tool. Show the current state too, when the epic moves something.

5. **Open it as a PR** in that repo, so it's reviewed like code, and give the user its link. Iterate on their review. Later phases link to it; it can't be attached to the tracker.

## Output

The design artifacts the epic needs: a standalone HTML prototype the user can open and share, an architecture or design-doc PR, or both.
