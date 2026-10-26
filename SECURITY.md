# Security policy

## Supported versions

Security fixes go into the latest release. Update to it before you report a problem, if you can.

## Reporting a vulnerability

Please don't open a public issue. Report it privately through GitHub instead: [report a vulnerability](https://github.com/Beakpoint-Insights/roost/security/advisories/new). Only the maintainers can see the report.

Tell us:

- which skill, script or workflow is affected, and the roost version;
- what an attacker could do, and how;
- the steps to reproduce it, with any team details replaced by made-up ones.

We'll confirm we've got it, keep you posted while we fix it, and credit you in the advisory unless you'd rather we didn't.

## What counts

roost is a set of instructions that coding agents follow, so its risks are mostly about what those agents can be led to do. For example:

- a skill that could send a secret, a token or a team's private details somewhere it shouldn't go;
- a skill that could run a command against staging, production, an outside service or a shared database, when roost says only you run those;
- text in a ticket, PR or comment that could make a skill do something its instructions don't allow;
- a problem in this repo's GitHub workflows or scripts.

Problems in Claude Code, the MCP servers or other tools roost uses belong with those projects.
