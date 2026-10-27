---
type: llm
---

The epic shipped two separate features. Paying by bank transfer reached customers on March 5, 2026 (acme-api's deploy that included #870; acme-web's #510 merged March 4). The yearly ZIP download reached customers on March 20, 2026 (acme-web's #522, which deploys on merge).

It passes when the reply gives two notes, one for each feature, the bank-transfer note dated March 5, 2026 and the ZIP-download note dated March 20, 2026, each complete with a title, a category and date line, and a body.

It fails if one note covers both features, if the bank-transfer note is dated March 20 or March 27, if either note is dated by the resolution date, or if the reply offers alternative versions of the same note.
