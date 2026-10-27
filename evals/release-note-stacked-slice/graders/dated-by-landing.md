---
type: llm
---

acme-web's last change for the feature, #486, merged on March 13 into another slice's branch, not into `main`; it reached `main`, and so production (acme-web deploys on merge), on March 19, through #491's squash commit 5e7a9c1. acme-api's last change reached production on March 13. Customers could use the whole feature from March 19, 2026.

It passes when the note is dated March 19, 2026, and the evidence table's acme-web row dates it by the change reaching `main` on March 19 (naming #491, 5e7a9c1, or the change reaching `main`).

It fails if the note is dated March 13 (#486's own merge), March 26, March 30, April 2 (the resolution date), if it has no date, or if acme-web's date is given as not found.
