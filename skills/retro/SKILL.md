---
name: retro
description: "Run a retro on one Claude Code session: read its transcript through a script that picks out the moments worth a finding (corrections, refusals, errors, retries, long searches, slow steps, stops for the user, blocks), turn them into one ranked list of setup changes, each with its evidence, what skipping it costs, a Checked or Hypothesis recommendation and where the change goes, and wait for the user's decision on each before giving the accepted ones a home: a config edit for the user, a ticket with a cross-repo-handoff prompt, or a person-owned task for a check only the user can run. Read-only until the user decides. Use when the user says \"retro on this session\", \"retro on <session name>\", \"what went wrong in that session\", \"lessons from this run\" or \"what should we change after that session\"."
---

# Retro

A run that went badly once will go badly again unless something in the setup changes: the team config, a repo's checks or instructions, or roost itself. The retro reads what actually happened in a session, finds the moments that cost time or trust, and proposes the change that stops each one recurring, in the place that can enforce it.

**First, load the team config with `roost-config`.**

For now the retro covers one session: this one, or one the user names. It reads only that session's own transcript, never a subagent's.

## Rules

- **Read-only until the user decides.** Before the checkpoint, never edit a file, the team config, a repo or roost, never file or change a ticket, and never message a session.
- **The retro never runs a check itself.** A hypothesis's check is run by the user or a repo session, or ticketed.
- **Every finding has evidence.** A finding whose problem isn't in the script's output, the transcript or the tracker isn't reported, however likely it seems.
- **Quotes come only from the script's output,** which is already redacted. Never paste text from the transcript into a finding, a ticket or a handoff; cite the moment's session and time instead.
- **The retro never edits the team config or a permission settings file.** An accepted config change or permission rule is shown for the user to make.

## 1. Find the transcript

If the user already gave you the script's output for the session, skip to step 3: don't look for the transcript or run the script again.

Transcripts are `~/.claude/projects/<folder>/<session id>.jsonl`, one folder per working directory. Don't build the folder's name from the path (characters such as `.`, `_` and spaces are changed in it); find transcripts by what their records say: each record has the session's working directory as `"cwd"`.

- **"This session":** the transcripts whose records have this working directory as their `cwd` (`grep -lF '"cwd":"<this directory>"' ~/.claude/projects/*/*.jsonl`, a fixed string, so `.` and `[` in the path match only themselves); of those, the newest that contains the user's last message. Say which file.
- **A named session:** search every folder under `~/.claude/projects/`, not only this directory's: a repo session's transcript is in its own repo's folder. Match the name against each transcript's `custom-title` and `agent-name` records, written with no space after the colon (`grep -lF '"customTitle":"<name>"' ~/.claude/projects/*/*.jsonl`, and the same for `"agentName":"<name>"`). If none matches, or more than one does, list what you found and ask which.

## 2. Run the script

```bash
python3 <this skill's folder>/scripts/retro_moments.py moments <transcript> --config <team config> [--config <override>]
```

The script is `skills/retro/scripts/retro_moments.py`; run it from this skill's own folder. Pass the team config and then each override file `roost-config` applied, in that order: the script redacts their identifying values (the tracker site and IDs, hostnames, URLs, IP addresses, the test account pattern) and generic secrets from every quote, and drops a quote it can't clean.

It prints one JSON object: `moments` (each with its kind, session, time, record id and excerpt; slow steps grouped by command with each run), `sessions` with `totals` per session, `unreadable` transcripts (files it couldn't open), `unparseable` records, `unknown_types`, `unknown_shapes` (records that look like a hook's block or a delivery notice, in a shape the script doesn't read yet), `subagents_not_read` and `redaction`.

## 3. Read the moments

Read every moment and the totals. Open the transcript around a moment only when the excerpt isn't enough to say what happened, and quote only the script's excerpt.

A `correction` moment is only a candidate: the script marks each message the user typed after their first, except the interruption a rejected permission prompt writes. A go-ahead or an approval ("yes", "proceed", "merged", "looks good") isn't a correction, and nor is the user's answer to a question the agent asked. Only a message that changes or rejects what the agent did ("we don't use moment here", "that's the wrong repo") can back a finding. The user interrupting the agent (`[Request interrupted by user`) is a real correction too: they stopped what it was doing.

A `refusal` moment is a tool call that didn't run; its `how` says who stopped it:

- **`user-rejected`:** the user said no at a permission prompt. That's the user's judgment, like a correction: the agent tried something they didn't want. The prompt's own "[Request interrupted by user for tool use]" isn't counted again.
- **`automode-blocked`** or **`automode-unavailable`:** auto mode stopped the call, not the user. Nobody said no to that call: it points at what the session was allowed to do, not at the user's view of the work, so its finding is in the **Permissions and auto mode** area of `references/finding-areas.md` (or **roost itself**, when a roost skill asked for the blocked action). An interruption after it is a real correction.

## 4. Write the findings

Use `references/finding-areas.md`: each finding names its area, which decides where the fix goes, and has what happened, its evidence (the moment's excerpt, session and time), what skipping it costs with a concrete case, a recommendation marked **Checked** or **Hypothesis**, and where the change goes. Rank them there too.

- A mechanical mistake is a check (a lint rule, a hook or a CI job in the repo); a review miss is a review rule (added to the repo's existing `review_focus`; when the repo has none, start from `planning.review_focus`, since a repo's own replaces it; or the repo's coding standards). Neither is only a line in `CLAUDE.md` or `AGENTS.md`.
- A slow step is one finding with its count and total, never one per run. A skip or a speed-up you can't prove from what you've read is a Hypothesis that names its check, who can run it and how long it takes.

## 5. The checkpoint

Show one ranked list, most severe first:

| # | Severity | Area | Finding | Evidence | What skipping costs | Recommendation | Where |
|---|---|---|---|---|---|---|---|

- **Severity:** High, Medium or Low.
- **Recommendation:** starts `Checked:` with its evidence, or `Hypothesis:` with the check, who can run it and how long it takes against what the problem costs.
- **Where:** `Team config` (and the key), a repo's name, `Permissions` (the settings file and the tool), or `roost`.

End with: "Decide each by number: a Checked finding takes yes or no; a Hypothesis takes check now, ticket the check, or skip." Then stop and wait.

A "yes" on a Hypothesis isn't one of its choices: ask again which of the three it is. Never treat it as approving the change: the change waits for the check.

## 6. Give each accepted finding a home

Only after the user decides, and only for what they accepted:

- **A team config change:** show the key and its new text for the user to make. Don't edit the config.
- **A permission rule:** name the settings file and the tool, with the moment's session and time, for the user to write the allow rule. Don't copy the command from the transcript, and don't edit any settings file.
- **A change in a repo:** a ticket for that repo with a `cross-repo-handoff` prompt that its session can act on.
- **A change to roost:** list it in the report for the user, with its evidence. Don't draft or file a roost issue: roost's tracker is public, and the retro doesn't yet swap the team's names for example names or check a draft for private details.
- **A hypothesis, "check now":** give the user the check's steps (or what to tell the repo session), wait for the result, then mark the finding Checked or drop it.
- **A hypothesis, "ticket the check":** ticket the check, not the change. A check a repo session can run is a ticket for that repo, with a `cross-repo-handoff` prompt. A check only the user can run is a person-owned task (labelled `tracker.person_task_label`, default `person-owned`) for the user, with its steps and the result that confirms or refutes the hypothesis. The change waits for that result.
- **Skipped or rejected:** nothing is filed.

## Report

One line: "Retro on acme-api-3f: 4 findings, 2 accepted, 1 check ticketed, 1 skipped." Then each home made, with its link. Then, when there are any, each of these, never skipped silently:

- **A transcript that couldn't be opened** (`unreadable`): which session, and why; the retro covers the rest. These are whole files, not the unreadable records below.
- **Unreadable records** (`unparseable`, `unknown_types`): "3 records couldn't be read (2 not JSON, 1 incomplete last line); 1 unknown record type."
- **Unknown shapes** (`unknown_shapes`): "2 records look like a hook's block; retro doesn't read that shape yet, so they aren't in the findings: <session>, lines 77 and 140."
- **Subagent transcripts** (`subagents_not_read`): "2 subagent transcripts weren't read; retro reads only the sessions' own transcripts."
- **Withheld quotes** (`redaction.dropped`): "2 quotes withheld; their findings cite the session and time."
