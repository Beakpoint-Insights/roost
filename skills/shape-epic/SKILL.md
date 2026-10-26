---
name: shape-epic
description: Shape a product idea into a fully-defined, buildable epic. Composable phases from problem statement through epic definition, design (a UI prototype, an architecture PR, or both), slice planning, test creation, build guide, and a tech lead handoff prompt attached to the epic. Can enter at any phase depending on what already exists. Use when user wants to go from idea to implementation-ready epic.
disable-model-invocation: false
argument-hint: "[PROJ-XXXX | phase-name]"
---

# Shape Epic

Turn a product idea into a fully-defined, buildable epic with its design (a UI prototype, an architecture or design-doc PR, or both), ordered slices, test scenarios, a visual build guide, and a tech lead prompt that hands the epic to developer agents.

## Trigger

- `/shape-epic` — auto-detect what exists, resume from there
- `/shape-epic PROJ-XXXX` — shape an existing epic
- `/shape-epic problem` — start from problem analysis
- `/shape-epic design` (or `prototype`) — design an existing epic: a UI prototype, an architecture PR, or both
- `/shape-epic slices` — plan slices for an epic that has its design
- `/shape-epic tests` — create test scenarios for existing slices
- `/shape-epic guide` — generate the build guide from existing slices and tests
- `/shape-epic handoff` — write the tech lead prompt and attach it to the epic

## Team config

**First, load the team config with `roost-config`.** The tracker and its project are in `tracker` (its adapter says how keys look), the design system is `design`, the repos the tech lead reads are `repos`, and the roadmap question uses `roadmap`.

## Rules for every phase

- **End every stop with the exact next step, as a question.** When you finish a phase or wait for feedback, the last line names what happens next by phase and skill, so the user knows what "yes" starts: "Next is Phase 4 (slices): I'll split PROJ-2961 into stories from the prototype. Start it, or change the prototype first?" Never end on "let me know" or "what next?".
- **Every question comes with your recommendation and why.** List the options with the recommended one first, so the user can answer with a letter. A question without a recommendation costs them a round trip.
- **Scope changes only when the user decides.** Anything you find while shaping that isn't part of the epic (a bug in existing code, a refactor, a gap in another feature) goes to the user as a proposed ticket: what it is, the evidence (`file:line`), and a recommendation (its own Bug, under this epic, or leave it). Don't fold a fix into the design, the slices or the description until they decide, and file the ticket once they do.
- **Work no repo session can do** (a PR to another company's repo, a video, a partner conversation, a launch post) is a person-owned task: see phase 4.

## Phases

The skill has seven composable phases. Each phase produces artifacts that feed the next. You can enter at any phase if the prerequisites exist.

```
problem → epic → design → slices → tests → guide → handoff
```

| Phase | Produces | Prerequisites | Steps |
|-------|----------|---------------|-------|
| 1. Problem | Structured problem statement | An idea, complaint, or observation | `references/phase-1-problem.md` |
| 2. Epic | Epic in the tracker, with a rich description | Problem statement (or user provides context) | `references/phase-2-epic.md` |
| 3. Design | The target state: an interactive HTML prototype for UI work, an architecture or design-doc PR for how the system is built or run, or both | Epic description with goals and scope | `references/phase-3-design.md` |
| 4. Slices | Ordered stories under the epic | Epic + design | `references/phase-4-slices.md` |
| 5. Tests | The tests for every slice, in the form the team's tests take | Slices (+ design for testable behaviors) | `references/phase-5-tests.md` |
| 6. Guide | Visual build-guide artifact | Slices + tests | `references/phase-6-guide.md` |
| 7. Handoff | Tech lead prompt, attached to the epic with the guide and the prototype (if any) | Slices + tests + guide + design | `references/phase-7-handoff.md` |

**Before starting a phase, read its steps file in full and follow it.** Each file holds that phase's process, guidance and expected output.

## Auto-Detection

When invoked without a specific phase, inspect what exists and recommend where to start:

1. **No epic key provided:** Ask if they have an existing epic or want to start from a problem statement.
2. **Epic key provided:** Fetch the epic and its children from the tracker.
   - Has stories under it? Skip to phase 5 or 6.
   - Has tests? Skip to phase 6.
   - Has a build guide but no `<EPIC> Tech Lead Prompt.md` attachment? Skip to phase 7.
   - Has only a description? Start at phase 3 (design) or phase 4 (slices).
3. Present what you found and propose the next phase. Let the user override.

```
I found PROJ-1768 with:
  ✓ Rich epic description (goals, scope, technical context)
  ✓ 5 stories (PROJ-1771 through 1775)
  ✓ 9 test issues
  ✗ No build guide artifact

Recommended next step: Phase 6 (Build Guide)
Want to proceed, or would you rather revisit an earlier phase?
```

---

---

## Resuming Partially-Defined Epics

This skill is designed for epics at any stage of definition. Common entry points:

| Situation | Start At |
|-----------|----------|
| "I have an idea but nothing in the tracker" | Phase 1 (Problem) |
| "I have an epic but it's just a title" | Phase 1 (Problem), then update the epic in Phase 2 |
| "Epic is well-defined but has no design" | Phase 3 (Design) |
| "We have stories but no tests" | Phase 5 (Tests) |
| "Everything exists, need the handoff doc" | Phase 6 (Guide) |
| "Guide exists, developers need to start" | Phase 7 (Handoff) |
| "We need to add more slices to an existing epic" | Phase 4 (Slices), preserving existing ones |
| "Tests exist but don't match the current slices" | Phase 5 (Tests), reviewing what exists first |

When entering mid-stream, always inventory what exists before proposing new work. Don't recreate what's already there.

---

## Quality Checklist

Before declaring a phase complete:

- [ ] User has reviewed and approved the output
- [ ] All tickets have rich descriptions (not just titles)
- [ ] Stories are ordered and independently shippable
- [ ] Tests cover every acceptance criterion in every slice
- [ ] Cross-cutting tests are identified and mapped to their last dependency
- [ ] The build guide accurately reflects the current state of all slices and tests
- [ ] The epic has the build guide, the prototype (if it has one) and the tech lead prompt attached, and a comment linking any design PR
- [ ] The tech lead prompt has no unfilled placeholders, and every "In this epic" line comes from this epic's own sources

## References

- See `references/epic-description-template.md` for the recommended epic description structure
- See `references/slice-checklist.md` for the slice quality checklist
- See `references/tech-lead-prompt-template.md` for the Phase 7 prompt template and how to fill it
- See `references/phase-<n>-<name>.md` for each phase's steps
- The tests adapter's "Create a test" says how Phase 5 creates tests
- The skill named in `roadmap.skill`, if any, puts an epic on the roadmap
