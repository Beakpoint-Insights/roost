---
name: cross-repo-handoff
description: Write a prompt that another repo's agent can run cold, for work this repo needs but must not do itself (for example the API change a UI fix depends on, or the UI change an API fix needs). Posts it as a comment on the ticket or returns it for pasting. Use when the user asks for "a prompt for the API agent", "a prompt for the UI agent", "what should I share back", or when a fix needs changes in the other repo.
---

# Cross-Repo Handoff

Each repo in the team's roost config (`repos`) has its own agent, often running at the same time. An agent never edits another repo. When a fix needs work over there, write a prompt the other agent can follow with no other context.

**First, load the team config with `roost-config`.** Each repo's `owns`, `contract`, `tests` and `e2e` say what belongs where and how it's tested.

## When to write one

- Your fix needs a change in the other repo. Finish what belongs to this repo, then write the handoff for the rest.
- The other agent asked you for something and you've done it. Write what they need to pick it up (the "share back" note).
- The user asks for a prompt to give the other agent.

Never edit, build or run tests in the other repo to "check quickly". Reading its code to understand a contract is fine.

## The prompt's shape

Write it as plain instructions to another engineer. Use this order and leave out sections that don't apply:

1. **Prerequisite:** what must land first, for example "Do this after the API work in the other comment, which adds `registrationOpen` to `GET /api/auth/config`." Say whether the two sides deploy together. A repo with `depends_on` goes after the repos it depends on.
2. **Repo and branch:** the repo, the branch name (starting with the ticket key), and which stack it goes on: "on top of the AuthKit stack (PR #156 and its descendants)". Say to open the PR on the stack with the "Stacked on #NNN" banner.
3. **Goal:** one or two sentences on the behaviour that changes, from the user's point of view.
4. **Changes:** by file, with paths and approximate line numbers, and the exact names of types, fields, routes and messages. Quote current code when that's clearer than describing it. Give literal values (URIs, error types, copy text), not "add an appropriate message".
5. **Contract:** for an API change, the exact request and response shapes, status codes and Problem Details types. For a UI change, which generated client methods to call and what each response means on screen.
6. **Tests, written first:** the failing tests to write and what each asserts, including the e2e scenario and its Xray tag where one exists.
7. **Run:** the exact commands to run before pushing (unit tests, lint, the e2e feature file with its flags).
8. **Report back:** what the other agent should hand back: commit SHA, branch, whether the local stack (`stack.services`) is running the new build, and anything in the contract that changed from this prompt.

## Share-back notes

When the other agent's request is done, the note leads with what they need to act:

- the commit SHA and branch, and whether the running server has it
- what changed in the contract, and what didn't ("Unchanged since you consumed it: …")
- anything that will show up unexpectedly, such as other endpoints arriving from a rebase

## Where it goes

- If there's a ticket, post the prompt as a comment on it, so it survives the session. When a fix touches more than one repo, post one comment per repo.
- If a diff already exists (written and tested, then reverted to avoid a collision), put the full diff in the comment and say it was tested and how.
- Also give the user the text, ready to paste.

## Rules

- Each prompt stands alone. Don't refer to "the conversation" or "as discussed".
- Don't hedge. If something isn't decided, say what's undecided and who decides.
- No em dashes; plain language.
