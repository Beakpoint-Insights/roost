#!/usr/bin/env python3
"""Plays back a scripted roost orchestrator session in the terminal, for the README demo.

demo/roost.tape drives it with VHS: VHS types the user's replies, and this prints roost's side.
The conversation is made up (the example team, Acme), based on real roost sessions.

Script lines (in SCRIPT below):
  > text     the user types this (VHS types it; we wait for Enter)
  * text     a roost message, with a bullet
  . text     a continuation line under the previous message
  ~ text     a tool call, dimmed
  # text     a heading for a progress update (green 🟢, yellow 🙋, red ⚠️)
  - text     a dimmed separator, e.g. time passing
  |a|b|c|    a table row (the first row is the header)
  (blank)    a blank line
"""
import sys
import time
import unicodedata

RESET, BOLD, DIM = "\033[0m", "\033[1m", "\033[2m"
ORANGE, GREEN, YELLOW, RED, CYAN = "\033[38;5;209m", "\033[38;5;114m", "\033[38;5;221m", "\033[38;5;203m", "\033[38;5;117m"

SCRIPT = """
> /roost:shape-epic Let customers invite teammates to their workspace
~ Read the team config (Acme: acme-api, acme-web, acme-docs) and the members code in both repos
* Phase 1, the problem: customers can't add teammates themselves.
. They email support to do it, and it takes a day.
. Goal: an admin invites someone by email, and they're working in the app minutes later.

|#|Question|Options, recommended first|
|1|Who can send invitations?|A) admins only  B) any member|
|2|How long does an invitation link last?|A) 7 days  B) it never expires|
|3|What if the email already has an account?|A) join on next sign-in  B) ask them to accept|
. Reply like: 1A 2A 3A
> 1A 2A 3A
* Created epic PROJ-1234 and a prototype that follows your existing Settings > Members screens.
* 4 slices, 9 Xray tests, and 1 person-owned task (the changelog post).
. Next: build-epic PROJ-1234 from your orchestrator session. Start it?
> build PROJ-1234
~ Found the sessions: API (acme-api), Web (acme-web), Docs (acme-docs)
* The tech lead's plan is back: acme-api/docs/plans/2026-10-23-proj-1234-invite-teammates.md
. 4 slices, backend first in each. Rollout needed: yes (1 migration, for the invitations table).
. Every finding cites its file and line.
. 1 open question: do pending invitations use up a seat? I recommend yes.
. Read the plan, then approve it, or tell me what to change.
> approve
* Kickoffs posted on all 4 stories. Slice 1 started in the API session.
. Updates every 5 minutes; say "stop" to end them.

#🟢 14:05 · PROJ-1235 · moving
. #612 CI 9/11 · migration applied to the local database.
- 5 minutes later
#🙋 YOUR TURN · 14:10 · PROJ-1235
. 1. Unlock your password manager, so the API session can sign its commits.
. It has finished slice 1's backend but can't commit it until then. The Web session is waiting.
> done
#🟢 14:16 · PROJ-1235 · moving
. Backend #612 green · the Web session is building the invite dialog.
> What's the status on PROJ-1234?

|Story|Slice|State|
|PROJ-1235|1. Invite by email|🔄 Frontend kickoff|
|PROJ-1236|2. Accept an invitation|⏳ Not started|
|PROJ-1237|3. Manage pending invites|⏳ Not started|
|PROJ-1238|4. Seats and limits|⏳ Not started|

. PROJ-1235:
|Step|State|Evidence|
|Backend kickoff|✅ Done|#612, checks pass|
|Frontend kickoff|🔄 In progress|PROJ-1235-frontend, 3 commits, no PR yet|
|Tests verified|⏳ Remaining||
|Code review|⏳ Remaining||
|Fixes|⏳ Remaining||
|Exploratory testing|⏳ Remaining||
|Slice done|⏳ Remaining||
. Next: finish the frontend kickoff (Web session), then check the slice.
- 20 minutes later
* Slice 1 checkpoint: 3 review findings, nothing failing.

|#|Finding|Recommendation|
|1|An invitation link still works after it's used|Fix now: introduced here|
|2|Invite errors aren't read out by screen readers|Fix now: blocks the goal|
|3|The members list loads every user at once|Ticket for later: older|
> as recommended
* 2 fixes in, test-first, and reviewed again. PROJ-1241 filed for later.
* Slice 1 hand-off: 2 items are still open. Where should they go?

|#|Item|Recommendation|Why|
|1|PROJ-1243 Invite email has no plain-text part|Next slice|Slice 2 sends the email|
|2|PROJ-1241 Members list loads every user|Later|Nothing in this epic touches it|
> ok
* Carry-over comment updated. All 3 epic tests still pass. Slice 2's kickoffs rewritten.
. Slice 2 started.
- slices 2 to 4
> What's the status on PROJ-1234?

|Story|Slice|State|
|PROJ-1235|1. Invite by email|✅ Done|
|PROJ-1236|2. Accept an invitation|✅ Done|
|PROJ-1237|3. Manage pending invites|✅ Done|
|PROJ-1238|4. Seats and limits|✅ Done|
. Carried over: before release 1, later 2.
. Next: review the whole epic, then close it out.
- 30 minutes later
* Whole-epic review: 6 findings, 3 fixed, 3 ticketed.
* Close-out: 4 tickets are still open under PROJ-1234.

|#|Ticket|Recommendation|Why|
|1|PROJ-1251 Expired invite page is a dead end|Before release|Breaks the main flow|
|2|PROJ-1241 Members list loads every user|Follow-up epic|Same screens, can wait|
|3|PROJ-1248 Lint warnings in the invite form|Standalone|Not about this feature|
|4|PROJ-1244 Changelog post|Stays: yours|Person-owned, after release|
> ok
* PROJ-1251 fixed on the stack. 2 tickets moved out, each with a link back.
. The epic has nothing open but the deploy ticket and your changelog post.
* Release QA in the Web session: 186 e2e scenarios pass, 6 exploratory charters.
. Ready, with 1 fix-soon bug (PROJ-1252). Release order: 7 PRs in 1 deploy.
> let's run the PROJ-1240 runbook together
~ Read docs/runbooks/proj-1234-rollout.md · 5 stages, each a sub-task of PROJ-1240
* Stage 1 of 5: Staging, apply the migration (PROJ-1245).
. Run this, then paste the output:
.   npm run migrate -- --env staging
. Expect: Applied 1 migration: 20261023_add_invitations
> Applied 1 migration: 20261023_add_invitations
* Pass. Recorded in your run copy; PROJ-1245 is Done.
* Stage 2 of 5: Staging, deploy. Merge the API stack first: gh stack merge 612 --squash
- stages 2 to 5
* Gate passed. Production runs PROJ-1234, and all 4 stories are Done.
. Left: your changelog post (PROJ-1244). Build guide updated to show what shipped.
"""


def out(text: str, pause: float = 0.06) -> None:
    sys.stdout.write(text + RESET + "\n")
    sys.stdout.flush()
    time.sleep(pause)


def width(text: str) -> int:
    """Columns the text takes on screen: wide characters such as emoji take two."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 0 if unicodedata.combining(c) or c == "\ufe0f" else 1 for c in text)


def pad(text: str, w: int) -> str:
    return text + " " * (w - width(text))


def table(rows: list[list[str]]) -> None:
    widths = [max(width(r[i]) for r in rows) for i in range(len(rows[0]))]
    line = lambda l, m, r: DIM + l + m.join("─" * (w + 2) for w in widths) + r
    out("  " + line("┌", "┬", "┐"), 0.03)
    for n, row in enumerate(rows):
        cells = [(BOLD if n == 0 else "") + f" {pad(c, w)} " + RESET for c, w in zip(row, widths)]
        out("  " + DIM + "│" + RESET + (DIM + "│" + RESET).join(cells) + DIM + "│", 0.12)
        if n == 0:
            out("  " + line("├", "┼", "┤"), 0.03)
    out("  " + line("└", "┴", "┘"), 0.3)


def main() -> None:
    rows: list[list[str]] = []
    for raw in SCRIPT.strip("\n").splitlines():
        if rows and not raw.startswith("|"):
            table(rows)
            rows = []
        kind, text = raw[:1], raw[2:] if len(raw) > 1 else ""
        if raw.startswith("|"):
            rows.append([c.strip() for c in raw[1:-1].split("|")])  # keep empty cells
        elif kind == ">":
            time.sleep(0.6)
            sys.stdout.write(f"\n{ORANGE}{BOLD}❯{RESET} ")
            sys.stdout.flush()
            input()  # VHS types the text
            time.sleep(0.5)
        elif kind == "*":
            out(f"{BOLD}●{RESET} {text}", 0.5)
        elif kind == ".":
            out(f"  {text}", 0.35)
        elif kind == "~":
            out(f"{DIM}  ⎿ {text}", 0.7)
        elif kind == "#":
            color = GREEN if "🟢" in raw else YELLOW if "🙋" in raw else RED
            out(f"\n{color}{BOLD}{raw[1:]}", 0.4)
        elif kind == "-":
            out(f"\n{DIM}  ⋯ {text} ⋯", 1.2)
        elif raw == "":
            out("", 0.1)
    if rows:
        table(rows)
    time.sleep(60)  # outlast the recording, so it never ends on a shell prompt


if __name__ == "__main__":
    main()
