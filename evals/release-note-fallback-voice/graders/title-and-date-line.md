---
type: llm
---

roost's fallback voice: the title is in Title Case, 2 to 7 words, and names the feature or what the customer gets, never the tracker's goal-style epic title. Under it is one line with the category and the date, written like "Fix · March 10, 2026". Categories are New, Improvement and Fix; this change fixes something that was broken (late files were rejected), so Fix is right, and Improvement is acceptable.

It passes when the title is Title Case and 2 to 7 words, isn't "Stop losing usage when uploads arrive late", and the line under it gives the category (Fix or Improvement) and March 10, 2026.

It fails if the title repeats the epic's title, is longer than 7 words, or is in sentence case; if there's no category and date line; or if the date is March 9 or March 12.
