---
type: llm
---

The run can't reach Jira, GitHub or the repos, so stopping on that is expected.

It passes when the reply does all of these:
- says this epic needs no UI prototype, because nothing a customer sees changes;
- proposes an architecture or design-doc artifact instead (for example ADRs and diagrams, opened as a PR);
- says where that doc would go, or asks the user where the team keeps such decisions.

Listing the design decisions the doc will cover, with options and recommendations, is fine, and so is asking the user to choose between them.

It fails if it builds, starts or offers an HTML prototype or UI mockups, or if it stops because the design system can't be reached.
