---
type: llm
---

The run is a retro on one session, from the moments script's output in the prompt. The reply should give one list of findings, ordered most severe first. Every finding has: what happened, its evidence (a quote or the moment's time or id), what skipping it costs, a recommendation marked Checked or Hypothesis, and where the change goes (the team config, the repo, or roost).

It passes when there is one ranked list, every finding carries all of those parts, and the unpaged `GET /api/usage` (a wrong result that review let through) ranks above the 14-call search.

It fails if findings are spread across several lists or paragraphs with no order, if any finding lacks evidence or a destination, if recommendations aren't marked Checked or Hypothesis, or if it invents a finding with no moment behind it.
