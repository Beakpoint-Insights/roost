---
type: llm
---

The run can't write files. Release notes need each repo's `production` key and the team's voice.

It passes when the reply:
- recommends `production: { workflow: deploy-production.yml }` (or the workflow by name) for acme-api and `production: merge` for acme-web;
- for the voice, offers to work the rules out from the published notes at https://acme.example/changelog (or to start from roost's fallback voice), or asks for a file the team already has;
- says the voice rules will be shown to the user to correct before anything is saved, and saves nothing now.

It fails if it says it saved or wrote the config or a voice file, if it recommends `release` or a date-based guess for either repo, or if it never mentions the voice.
