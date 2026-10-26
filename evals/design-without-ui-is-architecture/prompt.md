---
description: shape-epic's design phase, for an epic with no UI change, proposes an architecture or design-doc PR and builds no prototype.
tags: [shape-epic, design]
max_turns: 10
allowed_tools: [Read, Glob, Grep, Skill]
---

Our roost team config is the example config in the roost plugin, `examples/config.example.yml`.

Use shape-epic to run the design phase for epic PROJ-1300, "Run the API in our own cloud account". Goal: move the API and its workers from a managed hosting provider to Kubernetes in our own AWS account, with infrastructure as code, and switch production over with no downtime. Nothing a customer sees changes: no screens, no API changes. Out of scope: the database, which stays where it is.
