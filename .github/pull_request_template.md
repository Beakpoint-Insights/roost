## What changed and why

<!-- One or two sentences. Link the issue: "Closes #123". -->

## Checks

- [ ] The PR title is a Conventional Commit (`feat:`, `fix:`, `docs:` and so on). It becomes the commit message.
- [ ] `claude plugin validate --strict .` and `scripts/check-skills.sh` pass locally.
- [ ] If a skill's behavior changed, an eval case covers it and is tagged with the skill's name.
- [ ] No team's private details: examples use the Acme team and `PROJ-1234`.
- [ ] The README's tables match, if I added or changed a skill.
