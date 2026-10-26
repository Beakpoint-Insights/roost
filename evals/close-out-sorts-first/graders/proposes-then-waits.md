---
type: llm
---

The run can't reach Jira. The reply proposes a place for each of the three tickets the prompt names: fix before release, move to a follow-up epic, or make standalone, with a reason each. A sensible split keeps the onboarding accessibility bug before release, sends the API keys paging work to a follow-up epic, and makes the lint task standalone. It mentions linking moved tickets back to the epic or keeping their context, and it waits for the user's decision. It fails if it says it already moved, re-parented or closed any ticket, or doesn't distinguish follow-up epic from standalone.
