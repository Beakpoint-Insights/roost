---
type: llm
---

The whole reply is the update; grade all of it. It starts with the level-2 heading "## 🙋 YOUR TURN · 13:45 · PROJ-2789" (nothing above it). Directly under it is a numbered list whose first item is a bolded action telling the user to sign in to AWS, naming the command (`aws sso login --profile acme-dev`) and where to run it (the API session's terminal). After the list there are at most two plain lines of context (for example that the UI session is waiting on the API). It fails if the reply starts with anything else (a status line, a 🟢 heading, a table), if the heading lacks the time or the story, if the action is buried after context, if it has more than two lines of context, if it reports the API session as "working", or if there's any text after the update (an explanation, a note about notifications or logging, earlier updates).
