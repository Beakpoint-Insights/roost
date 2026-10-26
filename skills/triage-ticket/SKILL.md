---
name: triage-ticket
description: Decide whether a ticket (often a code-review or security finding) is accurate and needs fixing. Check each claim against the code, explain the real risk or failure scenario, and recommend fix or not. If the user says fix, fix it test-first with one commit per item. Use when the user asks to "review PROJ-X and help me determine whether we need to address it" or "is this accurate".
---

# Triage Ticket

Many tickets come from automated reviews. Some are right, some are half right, some are wrong. Find out which before anyone writes code.

**First, load the team config with `roost-config`.**

## 1. Read

- The ticket, its comments and its links.
- Split it into separate claims. A ticket with lettered or numbered items gets one row per item.

## 2. Check each claim against the code

- Find the code it's about and read it. Cite `file:line` for everything you conclude.
- Decide for each claim: **accurate**, **partly accurate** (say which part) or **wrong** (say why).
- For an accurate claim, describe the concrete scenario: who does what, in what order, and what goes wrong. For security findings, say who the attacker is, what they need, and what they gain.
- Say how likely and how bad it is, in plain terms: "anyone with an invitation link", "only during the migration window", "needs the signing key, which only the API has".

## 3. Recommend

Anything the user must do goes first, in its own block headed 🙋 **Your turn**: one line per action, saying exactly what and where. Leave the block out when there's nothing; never write "nothing needed". Don't hand the user anything you can do yourself (attaching files to the tracker, retitling a PR, checking a setting through a connected tool); only sign-ins, `vcs.signing_blocker` and decisions are theirs. Then start with the bottom line: "2 of 3 claims are real; fix A and B, skip C." Then a table:

| Item | Accurate? | What happens | Severity | Recommendation |
|---|---|---|---|---|
| A | Yes | … | Should fix before release | Fix: … |

- Give the fix in one or two sentences per item, with the file it touches.
- Where there's a manual alternative (for example "confirm the affected accounts by hand in the database"), say whether it fully removes the risk.
- Only include rows for the ticket's own claims. Don't add new findings to the table; list them separately, in one line each, if they matter.

## 4. Record the verdict in the tracker

Once the user agrees with the verdict, post it as a comment on the ticket, so the next person to open it can see why it was or wasn't fixed:
- the bottom line and the table from step 3
- the `file:line` evidence for each item
- the decision, and who made it: "<name of the person who decided>: fix A and B, skip C"

If the decision is not to fix anything, offer to close the ticket as `tracker.statuses.wont_do` (or the project's equivalent). Only transition it once the user says yes.

## 5. If the user says fix

- Move the ticket to `tracker.statuses.in_progress` when the work starts.
- Work on the branch the user names, or follow `stacked-prs` to put a new branch on the stack.
- One commit per item (signed, if `vcs.signed_commits`), test-first: a test that fails because of the problem, then the fix.
- Run the affected unit, functional and e2e tests, and report real counts.
- If an item needs another repo, don't touch it: write the hand-off with `cross-repo-handoff`.
- Concerns that come up while fixing, which aren't in the ticket, become new tickets when the user agrees. Each gets the epic as its parent (set at creation), Components, and a "relates to" link to this ticket.
- When every item is fixed and pushed, add a short comment listing each item with its commit, and move the ticket to `tracker.statuses.ready_for_release`. If an item was handed to another repo, leave the ticket where it is and say so in the comment.

## Rules

- Don't defend or attack the ticket; check it.
- Don't bring up topics the user didn't ask about.
- When asked "describe the tests you added", list each test by name with what it proves.
