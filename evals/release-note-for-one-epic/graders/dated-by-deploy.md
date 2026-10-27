---
type: llm
---

The feature needed changes in two repos. acme-api reached production on March 3, 2026 (the deploy-production.yml run that included #820, its last PR); acme-web deploys on merge, so its last change was live on March 2. Customers could use the whole feature from March 3, 2026.

It passes when the note is dated March 3, 2026, and the reply shows the evidence in a table with a row for each repo (its last change, the deploy or merge, and the date).

It fails if the note is dated March 17 (the resolution date), February 27 or 28, or March 2, if it has no date, or if there's no evidence table.
