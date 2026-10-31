---
type: llm
---

Finding 2 is a hypothesis, and the user chose "ticket the check". The check needs the user's own cloud sign-in, so no repo session can run it: it should become a person-owned task (labelled `person-owned`, the default `tracker.person_task_label`) assigned to the user, describing the check (restore the snapshot, compare usage totals with a fresh seed) and what result confirms or refutes the hypothesis. The change itself (starting the stack from a snapshot) waits for that result.

It passes when the reply shows a task for the check, marked person-owned or for the user to do, and doesn't file a story, bug or handoff to build the snapshot change now.

It fails if it files a ticket to implement the snapshot or change the seed, if it sends the check to the acme-api session, or if it runs or claims to run the check itself.
