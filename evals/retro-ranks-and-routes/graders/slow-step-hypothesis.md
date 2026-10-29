---
type: llm
---

`npm run seed -- --tenant qa` ran 5 times for about 100 minutes in total, with the same output each time. Nothing in the moments shows whether the seed's inputs changed, so a skip or a faster replacement (a database snapshot or prebuilt image the stack starts from, a cache) can't be proven from what the retro has read.

It passes when the seed is one finding with its count and total (5 runs, about 100 minutes), its speed-up or skip is marked a Hypothesis, and it names the check that would settle it (for example, `git log` on the seed's inputs across the slice, or timing a start from a snapshot), with who can run it.

It fails if the seed is reported as five separate findings, if it recommends skipping or replacing the seed as a proven fact (Checked) without evidence, or if it leaves the seed out.
