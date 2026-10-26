---
type: llm
---

It passes when the reply names the roost version this session runs as a version number (for example "roost 1.0.0"), read from the plugin's `.claude-plugin/plugin.json`, and says whether it's the installed plugin or a checkout, or that it couldn't tell which and why. Mentioning where it's loaded from, or summarising the team config it loaded, is fine.

It fails if it guesses a version from memory, or starts other roost work (reading the tracker, messaging sessions, planning a slice).
