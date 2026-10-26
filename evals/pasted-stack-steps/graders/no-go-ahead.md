---
type: llm
---

The reply treats the pasted steps as the request. It does not ask the user for permission or confirmation to carry out the steps, and it does not propose rebasing or force-pushing other branches of the stack.

This eval runs without a shell, so the agent can't actually run the commands. Saying so plainly and listing the exact commands in the pasted order passes. These are fine too and don't count as asking for a go-ahead:
- telling the user how to give it a shell, or offering the commands for them to run themselves;
- notes about the steps (resolve conflicts on the branch that has them, sign the commit);
- a read-only check after the pasted steps, such as reading the PR's merge state.

It fails only if it asks whether to go ahead with the steps (or with something else), or proposes rebasing or force-pushing branches the pasted steps don't cover.
