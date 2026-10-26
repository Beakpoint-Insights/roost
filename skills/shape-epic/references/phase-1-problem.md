# Phase 1: Problem Analysis

**Input:** A rough idea, user complaint, observed friction, or vague request.

**Goal:** Produce a structured problem statement that's specific enough to design against.

## Process

1. Listen to what the user describes. Ask clarifying questions, but keep it conversational (2-3 questions max per round).

2. **When the user names an existing system** (a platform you're moving off, a service, a pipeline), look at it before you assume how it works: read the repo in `repos` that owns it, and the live environment, read-only (listing and describing commands only; nothing that changes it). Record what you find with its evidence (`file:line`, or the command and its output) in Technical Context, and say where it differs from what was assumed: unused resources, dead config, what it really runs and uses. If you can't reach it, say so, and mark those facts as unchecked.

3. Structure the problem into these sections:

| Section | What It Contains |
|---------|-----------------|
| **Summary** | One sentence: what's wrong and who it affects |
| **Problem Statement** | 2-3 paragraphs: the gap between what users need and what the system provides. Use Don Norman's "gulf of evaluation" framing when it fits: what information is the user missing? |
| **Goals** | 3-5 numbered goals, each measurable or at least observable |
| **Real-World Failure Case** | One specific incident or scenario that illustrates the problem. Dates, actors, what happened, what should have happened. If no real incident exists, construct a realistic scenario. |
| **Technical Context** | What systems, tables, APIs, or data sources are involved. What the user needs to understand about how the current system works. |
| **Scope** | What's in, what's out. Be explicit about boundaries. |
| **Success Metrics** | How you'll know this is solved. Prefer behavioral metrics ("user can answer X without leaving the dashboard") over vanity metrics. |

4. Present the structured problem to the user. Iterate until they're satisfied.

## Output

A markdown document with the sections above. This becomes the epic description in Phase 2.
