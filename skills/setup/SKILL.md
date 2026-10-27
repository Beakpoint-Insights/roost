---
name: setup
description: Set up roost for a team. Links an existing team config, or makes a new one by asking about the team's tracker (Jira or GitHub Issues), tests, repos and how each reaches production, local stack, branching and deploy rules, and release notes (where they're published, and the team's voice), leaving out what the team doesn't have, then checks it. Use when a roost skill says there's no config, or the user says "set up roost", "configure roost", "roost for our team" or "change our roost config".
---

# Set Up roost

Every roost skill reads one team config (see `roost-config`). This skill puts one in place.

## 1. Is there one already?

Look where `roost-config` looks: a path the user named, `$ROOST_CONFIG`, `.roost/config.yml` from here up to the repo root, then `~/.claude/roost/config.yml`. If one exists, say which, and ask whether they want to change it or start again. To change one part (getting ready for release notes, say), ask only the questions for that part (step 3), show the lines that would change, and save nothing until the user agrees.

## 2. Link the team's config, if there is one

Most teams keep one config in a private repo so everyone uses the same. Ask whether the team has one. If so:

```bash
mkdir -p ~/.claude/roost
ln -s <path to the team's config.yml> ~/.claude/roost/config.yml
```

A link follows the clone, so `git pull` there updates everyone's config. If this machine differs from the others (its own database, other ports), put only those values in `~/.claude/roost/local/<team.name>.yml` rather than editing the shared file (`config-schema.md`, "Machine overrides"). Go to step 4.

## 3. Make a new one

Start from an example in the roost plugin: `examples/config.example.yml` for a team on Jira with an app and a local stack, or `examples/config.github-only.yml` for one that uses only GitHub (issues, eval cases, plain PRs, no stack or deploys). `skills/roost-config/references/config-schema.md` says what each key means. Ask in a few short rounds, not one long form, and recommend an answer wherever the code can tell you:

1. **Tracker:** Jira or GitHub Issues.
   - **Jira:** the site and project key, and the workflow's status names. Get the cloud ID with the Atlassian MCP's `getAccessibleAtlassianResources`.
   - **GitHub Issues:** the `owner/repo` whose issues are the tracker, and whether the organisation has issue types (`gh api orgs/<owner>/issue-types` lists them). Statuses other than open and closed are labels; suggest names.

   Either way, ask whether there's a status between merged and done (like "Ready for Release"), and whether every ticket needs Components.
2. **Tests:** Xray, or eval cases in the repo (a Claude Code plugin's `evals/`, run with `claude plugin eval`). For Xray, whether `XRAY_CLIENT_ID` and `XRAY_CLIENT_SECRET` are set; for evals, the folder and the command that runs one case.
3. **Repos:** each repo a story can touch, its GitHub `owner/repo`, its role, which goes first, and how one consumes another's work (a generated client, a shared package, nothing). Read each repo's README, package files and test folders to suggest `owns`, `tests` and the e2e commands. For each repo, recommend how it reaches production (`production`), say why, and ask: a workflow in `.github/workflows/` that runs on a release, a tag or a production deploy → `{ workflow: <file> }`; published releases and no deploy workflow (`gh release list`) → `release`; a host that deploys every merge to `main` (Vercel, Netlify, a deploy-on-push setting) → `merge`. Never recommend from dates.
4. **Local stack,** if there is one (a plugin or a library may have none; leave `stack` out): how they run everything locally, the services and their URLs, how to read flag state and logs, and how local migrations are applied. Read compose files, AppHost projects or scripts in the repos to suggest these.
5. **Branching:** whether they stack PRs with `gh stack` (`vcs.stacking: gh-stack`) or ship each branch as its own PR against `main` (`none`), sign commits, and require Conventional Commit titles. Read the repos' CI for a title check.
6. **Planning and deploy:** which repo the tech lead plans in and where plans go. If something is deployed (leave `deploy` out if not): where runbooks go, whether deploys run migrations, and where deployed logs live.

   **Release notes,** for a team that publishes customer-facing notes (leave `release_notes` out if not): the page where they're published (`release_notes.published_url`), and the team's voice (`release_notes.voice`). For the voice, ask for a path to the team's own voice file, or offer to work the rules out from the published notes, starting from `skills/release-notes/references/fallback-voice.md` and changing what the posts do differently. Show the whole voice file for the user to correct before anything is saved; never save voice rules the user hasn't seen.
7. **Design and roadmap:** the design system, if any, and whether epics go on a roadmap and which skill puts them there.

Leave out what doesn't apply: `stack`, `deploy`, `release_notes`, `design`, `qa` and `roadmap` are optional, and skills skip what needs a section that isn't there. Write the file where the user wants it: `~/.claude/roost/config.yml` for just them, or the team's private repo with a link (step 2) so everyone shares it.

**Never put a secret in the config:** no tokens, passwords or connection strings. It names where a secret comes from, never its value.

## 4. Check it

Read it back through `roost-config` and confirm:

- `tracker.kind`, `tests.kind` and `vcs.stacking` are supported (`roost-config` step 2 lists them);
- `gh repo view` works for every repo;
- **for GitHub Issues:** `gh issue list -R <tracker.github.repo> --limit 1` works, and the labels the config uses exist (the kinds, unless there are issue types; each status label; the Components prefix). Offer to create any that are missing with `gh label create`;
- **for Jira:** the Atlassian MCP can read the project (`getVisibleJiraProjects`), and `JIRA_EMAIL` and `JIRA_API_TOKEN` are set, and `curl -s -o /dev/null -w '%{http_code}' -u "$JIRA_EMAIL:$JIRA_API_TOKEN" https://<tracker.jira.site>/rest/api/3/myself` returns 200 (never print the token). Without them, attachments, parent changes and comment edits fall back to the shared signed-in browser; recommend setting them, with the link to create a token (https://id.atlassian.com/manage-profile/security/api-tokens);
- **for eval cases:** `tests.evals.dir` exists in the repo that holds them, and `claude plugin validate --strict .` passes there;
- every `stack.services` URL answers, if the config has a stack and it's running now (say so if it isn't);
- every repo has a distinct `name` and `order`;
- every `{ workflow: <file> }` in a repo's `production` exists in that repo (`gh api repos/<owner/repo>/contents/.github/workflows/<file>`);
- if `release_notes.voice` is set, its file exists, relative to the config file's folder;
- every skill the config names (such as `roadmap.skill`) is installed in this session, and if not, which plugin to install;
- if there's an app to test in a browser, or the tracker is Jira: the Playwright MCP is set up (for browser testing, and for Jira only as the fallback), and whether an isolated one (started with `--isolated`) is set up for local checks. Recommend adding one if not: several sessions share the signed-in browser, and only one can use it at a time.

Report one table: each area, its main values, and whether it checked out.
