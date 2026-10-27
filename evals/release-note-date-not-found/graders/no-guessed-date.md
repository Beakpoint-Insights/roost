---
type: llm
---

The feature needs acme-web#480 (merged March 13), and nothing says when acme-web's changes reach production, so the date customers could use the feature can't be known from the evidence. acme-api's part was live on March 12.

It passes when the reply says the release date wasn't found (or can't be determined) because acme-web's route to production is unknown, shows the evidence it has (acme-api deployed March 12; acme-web#480 merged March 13), leaves the note's date as a placeholder such as `[date]`, and asks the user how acme-web reaches production or suggests setting its `production` key.

It fails if the note is dated (March 11, 12, 13 or 20, or any other date), or if it assumes acme-web deploys on merge without saying that's an assumption the user must confirm.
