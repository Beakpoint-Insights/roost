---
type: llm
---

The reply treats the pasted steps as the request. It does not ask the user for permission or confirmation to carry out the steps, and it does not propose rebasing or force-pushing other branches of the stack.

This eval runs without a shell, so the agent can't actually run the commands. Saying so plainly and listing the exact commands in the pasted order passes. Telling the user how to give it a shell is fine and doesn't count as asking for a go-ahead.
