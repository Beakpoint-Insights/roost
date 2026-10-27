---
type: llm
---

The run can't reach Jira or GitHub. This is close-out-epic's after-release step: it confirms production runs the epic's code (acme-api through its deploy-production.yml run on March 3; acme-web deploys on merge, so March 2), deals with PROJ-2403 (closing it with acme-api 3.21.0 as its fix version, or saying it must be), and then offers to draft the epic's release note.

It passes when the reply confirms production from those two facts, handles or names PROJ-2403, and offers to draft PROJ-2400's release note (with the release-notes skill, or in words such as "Want me to draft the release note?").

It fails if the reply writes a release note (a title and body for customers) without being asked, if it never offers one, or if it says the epic isn't in production yet.
