#!/usr/bin/env python3
"""Plays back roost building roost, in the terminal, for the README demo.

VHS records it: VHS types the user's replies, and this prints roost's side. SCRIPT below is the only
copy of the conversation; `--tape` writes demo/roost.tape from it, with the typing speed and the
waits worked out from what each reply makes roost print. Re-record the README's GIF from the repo root:

  python3 demo/replay.py --tape > demo/roost.tape && vhs demo/roost.tape && gifsicle -b -O3 --colors 64 --lossy=30 demo/roost.gif

gifsicle (https://www.lcdf.org/gifsicle/) shrinks the GIF to about half, so the README loads quickly.
The conversation is real: epic #56 (release notes), from shaping to close-out, Oct 26 to 28, 2026.
It's condensed. The user's replies are theirs; roost's messages are shortened from what it said,
and long stretches of work are cut, marked with a "-" line.

Script lines (in SCRIPT below):
  > text     the user types this (VHS types it from the tape; we wait for Enter)
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
> /roost:shape-epic #56, where we want to have roost start producing release notes
~ Read #56, the team config (GitHub Issues, eval cases as tests, plain PRs) and the skills it touches
* #56 tells the problem well, but it isn't buildable yet: no goals, no scope, no stories, no tests.
. Its fallback voice is one company's own, sign-offs and all. Shipped in roost, every team would sound like it.
. I recommend: rewrite #56 as an epic, and make roost's fallback voice generic.
> i agree with everything you just said. please proceed.
* #56 is rewritten. The design needs 6 decisions:

|#|Decision|Options, recommended first|
|1|Where a repo's production date comes from|A) a key on each repo  B) a map under release_notes|
|2|How the team's voice is set|A) one Markdown file  B) three keys|
|3|Where the published notes are|A) a URL the skill reads  B) a URL or a file|
|4|How flags are found|A) read the merged diffs  B) a flag_patterns key|
|5|How catch-up finds candidates|A) from the tracker  B) from deploys|
|6|The skill's files|A) SKILL.md plus the fallback voice  B) one file|
> 1. i prefer a  2. i prefer a  3. i agree  4. i prefer a  5. i prefer a  6. i prefer a
* Design PR #58 is merged. #56 now has 4 stories, each with its eval cases written before any code:

|Story|Slice|Eval cases|
|#60|One epic's note, dated by when customers could use it|4|
|#61|Hold what customers can't use yet, and skip what's announced|3|
|#62|The team's own voice|3|
|#63|Catch-up since a date|1|
. The build guide and the tech lead prompt are in docs/design/. Next: build-epic #56.
- the next morning, in an orchestrator session
> /roost:build-epic #56
~ Found the worker session: roost (~/src/Beakpoint/roost)
* The tech lead's plan is PR #70. 1 open question: should roost's generic rules fill gaps in a team's own voice file?
. I recommend no: the team's file is the whole voice. Reply "approve", or tell me what to change.
> I agree -> the team's file is the whole voice. approve
* Kickoffs posted on #60 to #63. #60 started in the roost session.
. Updates every 5 minutes; say "stop" to end them.
- 4 hours later
> i just got back after a break. bring me up to speed on #56 and #60

|Story|Slice|State|
|#60|1|⏸️  Code-review checkpoint, PR #71|
|#61|2|⏳ Not started|
|#62|3|⏳ Not started|
|#63|4|⏳ Not started|

|Step|State|Evidence|
|Kickoff and build|✅|PR #71, 7 commits|
|Tests verified|✅|All 4 eval cases pass 3 of 3|
|Real-data check|✅|roost's own #52 dated Oct 26, from roost-v1.2.0|
|Code review|⏸️ |12 findings, waiting on you|
#🙋 YOUR TURN · #60
. 1. Say "go" on the review table, or tell me what to change.
> okay go
- #60 merged (PR #71) · #61 at its checkpoint
* #61's review: 11 findings. One is a product question:
. A slice the feature needs is still being built when the rest ships. Hold the note (recommended), or leave it out?

|#|Finding|Recommendation|
|2|A flag switched on before the deploy dates the note too early|Fix: use the later date|
|4|A slice still being built is dropped, not held|Fix, per your answer|
|6|Any on/off switch counts as a flag, even an emergency off-switch|Fix: only a real flag holds it|
> Hold the note when it's still being built. #6 disagree, feature flags are different than circuit breakers. if there's trouble classifying, ask the developer - don't simply assume
* Your decisions are on #61's checkpoint comment, #6 in your own words. The roost session is making fixes 1 to 6.
. #6, done your way: a feature flag holds the note and a circuit breaker doesn't. When the code doesn't
. make clear which one a switch is, the skill asks the developer and doesn't guess.
- #61 merged (PR #74) · #62 merged (PR #76)
* #62 is done: #76 is merged, and release PR #73 now carries #60 to #62. What #62 left open:

|#|Leftover|Recommendation|
|1|A symlinked config needs a shell to find the voice file, or the fallback is used|Later|
|2|Nothing tests that two notes get different sign-offs. You declined that case earlier|Later|
|3|A flaky eval case on main, unrelated to #62|Ticket #84|
> 1. agree, later  2. agree, later  3. yes, we created a ticket
- #63 · catch-up since a date
* #63's review: catch-up reads Jira results from files, but the Jira connector puts them in the chat.
. The model has to copy every page into a file by hand: slow, costly, and it can silently drop tickets.
. (a) pass the results straight to the script  (b) the script calls Jira itself, with paging in tested code
> yes, definitely do b. avoid all that token usage
- #63 merged (PR #86) · review-epic #56
* Whole-epic review: the security review found nothing. The code review found 8 problems, one serious:
. Catch-up misses shipped work. Done Jan 30 and live Feb 3? A catch-up since Feb 1 never announces it.

|#|Your call|Recommendation|
|1|How far back catch-up looks|A) to the last post, or 90 days  B) 90 days|
|2|A new eval case for it|Yes|
> 1a 2yes
* PR #98 fixes all 8. The new eval case fails on main and passes 3 of 3 with the fix.
- release and close-out
* roost 1.3.0 is published with #60 to #63. #56 is closed: 5 items to follow-up epic #103, 2 standalone.
. A miss found after the release, bug #101, is fixed in PR #102 and ships as roost 1.3.1.
> alright i think we're done. thanks.
* Thanks, Alan. The build is done and the progress updates are off.
"""


# How long the reader gets after roost finishes printing a reply's answer: a skim at about
# 6 words a second, between these bounds. The whole wait after Enter is capped at MAX_WAIT.
MIN_READ, MAX_READ, MAX_WAIT = 2.0, 5.0, 8.0
# Replies type at TYPING_MS a character, faster for long ones so none takes over MAX_TYPING seconds.
TYPING_MS, MAX_TYPING = 45, 3.0

DRY_RUN = False  # --tape: run the script without printing or sleeping, adding up the pauses
clock = 0.0


def pause(seconds: float) -> None:
    global clock
    clock += seconds
    if not DRY_RUN:
        time.sleep(seconds)


def out(text: str, wait: float = 0.06) -> None:
    if not DRY_RUN:
        sys.stdout.write(text + RESET + "\n")
        sys.stdout.flush()
    pause(wait)


def width(text: str) -> int:
    """Columns the text takes on screen: wide characters such as emoji take two.
    The terminal moves one column for a narrow character shown as an emoji (⏸️), though it draws
    two, so the script puts a space after one."""
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


def play(on_reply=lambda reply: None) -> None:
    """Runs SCRIPT. on_reply is called at each "> " line, before the user types it."""
    rows: list[list[str]] = []
    for raw in SCRIPT.strip("\n").splitlines():
        if rows and not raw.startswith("|"):
            table(rows)
            rows = []
        kind, text = raw[:1], raw[2:] if len(raw) > 1 else ""
        if raw.startswith("|"):
            rows.append([c.strip() for c in raw[1:-1].split("|")])  # keep empty cells
        elif kind == ">":
            pause(0.6)
            on_reply(text)
            if not DRY_RUN:
                sys.stdout.write(f"\n{ORANGE}{BOLD}❯{RESET} ")
                sys.stdout.flush()
                input()  # VHS types the text
            pause(0.5)
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


TAPE_HEADER = """# The README demo, written by `python3 demo/replay.py --tape`. Don't edit this .tape file: change SCRIPT in
# demo/replay.py and write it again. To re-record the GIF, from the repo root:
#
#   python3 demo/replay.py --tape > demo/roost.tape && vhs demo/roost.tape && gifsicle -b -O3 --colors 64 --lossy=30 demo/roost.gif

Output demo/roost.gif

Set Shell "bash"
Set FontSize 16
Set Width 1300
Set Height 860
Set Padding 24
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set WindowBar Colorful
Set WindowBarSize 36
Set Framerate 15

Hide
Type "clear && python3 demo/replay.py" Enter
Sleep 1s
Show

Sleep 1s
"""


def tape() -> str:
    """The VHS tape: types each reply, then waits while roost prints its answer and it's read."""
    global DRY_RUN, clock
    DRY_RUN = True
    replies: list[tuple[str, float, int]] = []  # (reply, when it's typed, words printed since)
    printed = {"words": 0}
    real_out = globals()["out"]

    def counting_out(text: str, wait: float = 0.06) -> None:
        printed["words"] += len(text.split())
        real_out(text, wait)

    def on_reply(reply: str) -> None:
        replies.append((reply, clock, printed["words"]))

    globals()["out"] = counting_out
    play(on_reply)
    globals()["out"] = real_out
    replies.append(("", clock, printed["words"]))  # the end, to time the last answer

    lines = [TAPE_HEADER]
    for (reply, start, words), (_, end, words_after) in zip(replies, replies[1:]):
        if '"' in reply:
            raise SystemExit(f"a reply can't contain a double quote: {reply}")
        ms = min(TYPING_MS, int(MAX_TYPING * 1000 / max(len(reply), 1)))
        typing = f"Type@{ms}ms" if ms < TYPING_MS else "Type"
        read = min(MAX_READ, max(MIN_READ, (words_after - words) / 6))
        wait = min(MAX_WAIT, end - start + read)
        lines.append(f'{typing} "{reply}"\nSleep 500ms\nEnter\nSleep {wait:.1f}s\n')
    return "\n".join(lines)


def main() -> None:
    if sys.argv[1:] == ["--tape"]:
        sys.stdout.write(tape())
        return
    play()
    time.sleep(60)  # outlast the recording, so it never ends on a shell prompt


if __name__ == "__main__":
    main()
