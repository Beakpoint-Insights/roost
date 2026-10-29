# Finding areas, ranking and recommendations

What `retro` uses to turn moments into findings. Every finding names one area; its destination follows from the area.

## The eight areas

| Area | What counts | Where the fix goes |
|---|---|---|
| **Finding things** | A long `search` for a file or fact that a pointer would have saved | The repo's agent instructions, or the team config (`repos[].owns`, `stack`) |
| **Automated checks** | A mistake a deterministic check could catch: a banned API, a file location, an import shape. A repo with no checks at all is a finding in itself | A lint rule, hook or CI job in the repo, never a sentence in a doc |
| **Review rules** | Something a review let through that a standing rule should have caught | The repo's `review_focus` (team config) or its coding standards |
| **Agent instructions** | `CLAUDE.md`/`AGENTS.md` content the agent ignored, that's too long, or belongs in standards or a check | The repo |
| **Tool use** | Expensive or repeated calls that a script or a narrower command could replace | The repo (a script), or roost (a skill's step) |
| **Slow steps** | A step the run waits on, every time, that could be safely skipped or safely sped up: a large data import, a full build, a stack that starts from scratch, a test suite run whole when a few tests cover the change | The team config (`stack.test_data`, `stack.how`, a repo's `tests`), the repo (an image, a cache, a test selector), or roost (a skill that runs a step it could skip) |
| **Access** | Information the agent needed and couldn't get (server logs, a read-only view of a service) | The team config (`stack.telemetry`, a read command) or a person-owned setup task |
| **roost itself** | A skill that stopped when it shouldn't have, didn't stop when it should, guessed, or asked something it could have read | roost, as an issue |

A mechanical mistake becomes a check, and a review miss becomes a review rule, so the fix binds whoever can enforce it. Neither is ever only a new line in `CLAUDE.md` or `AGENTS.md`: the agent that made the mistake had instructions already.

### An example of each (the Acme team)

- **Finding things:** 14 `Grep`/`Read` calls over 6 minutes to find where acme-api builds its OpenAPI spec (scripts/openapi/build.ts). Fix: a pointer in acme-api's `CLAUDE.md`.
- **Automated checks:** the user corrected a `moment` import three times; acme-api uses date-fns. Fix: ESLint's `no-restricted-imports` for `moment` in acme-api, which fails in CI.
- **Review rules:** review passed `GET /api/usage` with no page size; the user caught it (2M rows for a big tenant). Fix: "list endpoints are paged" in acme-api's `review_focus`.
- **Agent instructions:** acme-web's `CLAUDE.md` is 900 lines and the agent missed its testing section twice. Fix: move the rules into acme-web's coding standards and keep `CLAUDE.md` to pointers.
- **Tool use:** the agent read the same 4,000-line migration log five times to find one table. Fix: a script in acme-api that prints a table's migrations.
- **Slow steps:** `npm run seed -- --tenant qa` ran 5 times, 100 minutes in all, with the same output each time. Fix (a Hypothesis until checked): start the stack from a snapshot of the seeded database.
- **Access:** the agent couldn't read the API's logs and asked the user to paste them three times. Fix: a read-only log command in `stack.telemetry`.
- **roost itself:** `run-slice` stopped to ask which branch to use, when the kickoff comment named it. Fix: a roost issue.

## Each finding's parts

Area, what happened, evidence (a quote from the script's output with its session and time, or a state-file or tracker line), what skipping it costs with a concrete case, the recommendation, and where the change goes.

**What skipping it costs** is concrete, not "it could cause problems": "the next list endpoint ships unpaged, and a big tenant's page load returns 2M rows", or "every slice spends another 20 minutes seeding, 100 minutes per epic of five".

A finding whose problem has no evidence in the transcripts or the tracker isn't reported, however likely it seems.

## Ranking

One list, most severe first:

- **High:** a wrong result shipped or nearly shipped, a trust break (the user had to check the agent's work to catch it), or a recurrence (an earlier retro's finding that came back unaddressed: one level higher than it would be, with "recurred: N runs").
- **Medium:** time lost on every run (a repeated search, a blocker, a slow step), or a skill misbehaving without a wrong result. A slow step ranks by its total across the run (a 20-minute import on each of five slices is 100 minutes), and is High when it's an hour or more per run.
- **Low:** one-off friction.

## Checked or Hypothesis

The problem always rests on evidence. The recommendation is one of two:

- **Checked:** the fix is confirmed from what the retro can read: the repo, `git log`, the transcripts, the tracker, the stack's config. Cite that evidence. For a slow step: what the step reads (a seed file, migrations, a dump URL), that `git log` shows none of it changed across the run, that its output was the same each time, that nothing using its result needs it freshly run, and whether the stack already keeps state (persistent containers, named volumes, a snapshot command).
- **Hypothesis:** there's a strong reason to think the fix is right, but confirming it means running something. Say what to run and which result confirms or refutes it, who can run it (a repo session, or only the user: production data, a signed-in service), and how long the check takes against what the problem costs per run.

A hypothesis ranks by what it would save if true, but keeps its label, so "saves 100 minutes, if…" never reads as a fact.

At the checkpoint, a hypothesis offers three choices:

1. **Check it now.** The user runs the check, or tells a repo session to. The retro waits, reads the result, and the finding becomes Checked or is dropped. The retro never runs the check itself.
2. **Ticket the check, not the change.** A check a repo session can run becomes a ticket for that repo, with a `cross-repo-handoff` prompt. A check only the user can run becomes a person-owned task (`tracker.person_task_label`) with the user as owner, its steps written out, and what result confirms or refutes the hypothesis. The change waits for the result.
3. **Skip.**

### A worked case

The seed above, as a Hypothesis: "Start the stack from a snapshot of the seeded qa tenant instead of seeding each time. Check: restore last month's snapshot from the shared backup bucket and confirm the usage totals match a fresh seed. Only the user can run it (the bucket needs their cloud sign-in); about 15 minutes, against about 100 minutes per epic. Skipping it costs 20 minutes on every slice."
