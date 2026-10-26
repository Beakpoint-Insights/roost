---
name: setup
description: Set up roost for a team. Links an existing team config, or makes a new one by asking about the team's tracker, repos, local stack, branching and deploy rules, then checks it. Use when a roost skill says there's no config, or the user says "set up roost", "configure roost", "roost for our team" or "change our roost config".
---

# Set Up roost

Every roost skill reads one team config (see `roost-config`). This skill puts one in place.

## 1. Is there one already?

Look where `roost-config` looks: a path the user named, `$ROOST_CONFIG`, `.roost/config.yml` from here up to the repo root, then `~/.claude/roost/config.yml`. If one exists, say which, and ask whether they want to change it or start again.

## 2. Link the team's config, if there is one

Most teams keep one config in a private repo so everyone uses the same. Ask whether the team has one. If so:

```bash
mkdir -p ~/.claude/roost
ln -s <path to the team's config.yml> ~/.claude/roost/config.yml
```

A link follows the clone, so `git pull` there updates everyone's config. If this machine differs from the others (its own database, other ports), put only those values in `~/.claude/roost/local.yml` rather than editing the shared file (`config-schema.md`, "Machine overrides"). Go to step 4.

## 3. Make a new one

Start from `examples/config.example.yml` in the roost plugin, and `skills/roost-config/references/config-schema.md` for what each key means. Ask in a few short rounds, not one long form, and recommend an answer wherever the code can tell you:

1. **Tracker:** the Jira site and project key, and the workflow's status names. Get the cloud ID with the Atlassian MCP's `getAccessibleAtlassianResources`. Ask whether there's a status between merged and done (like "Ready for Release"), and whether every ticket needs Components.
2. **Tests:** whether they use Xray, and whether `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set.
3. **Repos:** each repo a story can touch, its GitHub `owner/repo`, its role, which goes first, and how one consumes another's work (a generated client, a shared package, nothing). Read each repo's README, package files and test folders to suggest `owns`, `tests` and the e2e commands.
4. **Local stack:** how they run everything locally, the services and their URLs, how to read flag state and logs, and how local migrations are applied. Read compose files, AppHost projects or scripts in the repos to suggest these.
5. **Branching:** whether they stack PRs with `gh stack`, sign commits, and require Conventional Commit titles. Read the repos' CI for a title check.
6. **Planning and deploy:** which repo the tech lead plans in, where plans and runbooks go, whether deploys run migrations, and where deployed logs live.
7. **Design and roadmap:** the design system, if any, and whether epics go on a roadmap and which skill puts them there.

Leave out what doesn't apply. Write the file where the user wants it: `~/.claude/roost/config.yml` for just them, or the team's private repo with a link (step 2) so everyone shares it.

**Never put a secret in the config:** no tokens, passwords or connection strings. It names where a secret comes from, never its value.

## 4. Check it

Read it back through `roost-config` and confirm:

- `tracker.kind`, `tests.kind` and `vcs.stacking` are supported (`roost-config` step 2 lists them);
- the Atlassian MCP can read the project (`getVisibleJiraProjects`), and `gh repo view` works for every repo;
- `JIRA_EMAIL` and `JIRA_API_TOKEN` are set, and `curl -s -o /dev/null -w '%{http_code}' -u "$JIRA_EMAIL:$JIRA_API_TOKEN" https://<tracker.jira.site>/rest/api/3/myself` returns 200 (never print the token). Without them, attachments, parent changes and comment edits fall back to the shared signed-in browser; recommend setting them, with the link to create a token (https://id.atlassian.com/manage-profile/security/api-tokens);
- every `stack.services` URL answers, if the stack is running now (say so if it isn't);
- every repo has a distinct `name` and `order`;
- every skill the config names (such as `roadmap.skill`) is installed in this session, and if not, which plugin to install;
- the Playwright MCP is set up (for browser testing, and for Jira only as the fallback), and whether an isolated one (started with `--isolated`) is set up for local checks. Recommend adding one if not: several sessions share the signed-in browser, and only one can use it at a time.

Report one table: each area, its main values, and whether it checked out.
