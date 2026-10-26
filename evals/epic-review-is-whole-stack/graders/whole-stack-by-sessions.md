---
type: llm
---

The run has no shell, no Jira, no GitHub and no other sessions, so it can't actually do the review; stopping and saying what it would do, and what it needs, is the expected outcome. Pass if the reply describes reviewing the whole epic against main in each repo (not slice by slice), by the repo sessions rather than in this session, with extra attention to code that was never reviewed (such as the bug-fix PRs), and the findings going to the user for decisions before anything is fixed. Fail if it reviews or fixes code itself, plans to review only one slice or only the bug fixes, or treats the per-slice reviews as enough.
