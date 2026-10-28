---
type: llm
---

The run can't write files. Release notes need each repo's `production` key and the team's voice.

It passes when the reply:
- recommends `production: { workflow: deploy-production.yml }` (or the workflow by name) for acme-api and `production: merge` for acme-web;
- for the voice, offers to work the rules out from the published notes at https://acme.example/changelog (or to start from roost's fallback voice), or asks for a file the team already has;
- says the voice rules will be shown to the user to correct before anything is saved, and saves nothing now.

A voice file of the team's own, whatever it's named, shown before it's saved, isn't keeping Acme's example voice; only reusing the example's file or its rules is.

It fails if it says it saved or wrote the config or a voice file, if it recommends `release` or a date-based guess for either repo, if it never mentions the voice, or if it proposes keeping `voice: release-notes-voice.md`, Acme's example voice, for this team.
