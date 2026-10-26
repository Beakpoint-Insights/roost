# Phase 7: Tech Lead Handoff

**Input:** Slices + tests + build guide + the design (the prototype, the design-doc PR, or both), and the decisions made while shaping.

**Goal:** Write a self-contained prompt for a tech lead agent running in the lead repo (`planning.lead_repo`). That agent writes an implementation plan (`planning.plan_skill`) in a new `gh stack`, stops for the approval of the person running this skill, and then posts a kickoff comment for each repo on each story. Attach the prompt to the epic.

## Process

0. **Check how you'll attach files, first.** Before anything else, find out whether uploads will work ("Attach a file" in the tracker adapter): for Jira, whether `JIRA_EMAIL` and `JIRA_API_TOKEN` are set, or else whether the Playwright browser is signed in to the tracker. If neither, tell the user now, in a 🙋 **Your turn** line (set the token, or sign in), and carry on with the steps that don't need it. Don't find out at upload time.

1. **Get the artifacts onto the epic.** Developer agents can't open local files or private claude.ai links, so the epic needs these attachments:
   - `<EPIC> Build Guide.html`, the phase 6 guide
   - `<EPIC> Prototype.html`, the phase 3 prototype, if the epic has one

   Check the epic's attachments first. Upload any that are missing (see "Attaching files" below). A design-doc PR can't be attached: the prompt links it.

2. **Work out which repos the epic touches:** every repo named in its stories' `Repos:` lines (phase 4). A story shaped before those lines existed: work it out from its scope and confirm with the user. The prompt names only these repos; the rest of `repos` stays out of it.

3. **Read the code.** Look in each repo the epic touches for the files and classes each story touches, and for what's missing (endpoints, fields, flags). Every "Starting points" line and every "In this epic" line that describes code must come from this read, and must name a file.

4. **Fill in the template.** Use `references/tech-lead-prompt-template.md`.
   - Keep the fixed text word for word.
   - Fill every `{{PLACEHOLDER}}` and follow every `<!-- FILL -->` note, then delete the notes.
   - Write each checklist item's "*In this epic:*" line from this epic's own sources: the description, the decisions, the code, and the tracker links and their statuses. Don't carry over another epic's specifics.
   - Before you show it, check that no `{{` or `<!--` is left and that there are no em dashes.

5. **Review with the user.** Save the draft to `<team.drafts_dir>/<EPIC> Tech Lead Prompt.md` and tell the user what's in it, section by section. Update it until they approve.

6. **Attach and announce.**
   - Upload the approved file to the epic as `<EPIC> Tech Lead Prompt.md`.
   - Add a comment on the epic that names the prompt and the other attachments, links any design-doc PR, and says the next step is `build-epic` for this epic, run from the orchestrator session: it sends the prompt to the lead repo's session and brings the plan back for approval.

## Attaching files

Follow "Attach a file" in the tracker adapter.

## Output

`<EPIC> Tech Lead Prompt.md`, attached to the epic next to the build guide and the prototype (if any), plus a comment on the epic.
