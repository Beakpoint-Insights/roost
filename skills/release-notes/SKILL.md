---
name: release-notes
description: Draft customer-facing release notes for an epic that has shipped, ready to paste, one note per feature it shipped (usually one). Dates each note by when customers could first use the feature (the production deploy, release or merge that first carried its last change, shown in an evidence table), never by the tracker's resolution date; writes only what the slices built, listing anything cut; holds a note customers can't use yet (a feature flag, a slice not yet live, a correction to past data not yet run), saying what it waits for; checks the team's published notes so nothing is announced twice; leaves facts the evidence doesn't give as [N]; and writes in the team's voice (`release_notes.voice`), or roost's fallback voice without one. Never publishes or posts anything. Also catches up on everything released since a date, each epic's note oldest first, with standalone tickets listed for the user to pick. Use when the user says "catch us up on release notes since <date>", "what shipped since our last post", "draft the release note for PROJ-X", "write the release notes for this epic", "what do we tell customers about PROJ-X", and from close-out-epic once production runs the epic.
---

# Release Notes

A release note is public, and hard to take back once it's out. Each one has to be dated by when customers could actually use the feature, describe what was built (not what was planned), and leave anything the evidence doesn't say for the user to fill in. This skill gathers that evidence and drafts the note; the user publishes it.

**First, load the team config with `roost-config`,** and read its tracker adapter.

**Input:** the epic's key. Everything below calls it EPIC. Or a date, for everything released since then: see "Catch-up since a date" at the end, which runs steps 1 to 7 for each epic it finds.

**Evidence the user gives counts.** When the user has already given you facts (the tickets, the PRs, the deploy runs, a page's text), use them as read, and don't look them up again. Look up only what's missing. Whatever you couldn't read, from the user or the tools, goes in the checks (step 7), named.

**Never publish or post anything:** no tracker comments, no status changes, no posts. The reply is the draft.

## 1. Find the work

Read EPIC and its children (stories, tasks, bugs) through the tracker adapter, with their statuses. For each child that's at `tracker.statuses.done` or `tracker.statuses.ready_for_release` (a shipped ticket can still sit there), find the PRs that built it, in every repo in `repos`:

- the PRs that close it (a closing reference);
- PRs whose title, body or head branch has its exact key, written as the tracker adapter writes keys in text and in branch names ("Keys"). GitHub's search reads titles and bodies but not branch names, so look both ways: `gh pr list -R <repo> --state merged --search "<key>" --limit 1000 --json number,title,body,headRefName,baseRefName,mergeCommit,mergedAt` for titles and bodies, and the same without `--search`, filtered on `headRefName`, for branches (without `--limit`, `gh` stops at 30; if either returns exactly 1000, say so in the checks). Keep only the PRs where the key stands on its own, with no letter or digit right before or after it (`#60` doesn't match `#601`, `PROJ-2482` doesn't match `PROJ-24821`, and a bare `60` doesn't count). The one exception is a cross-repo reference to the tracker's own repo: `owner/repo#60` counts when `owner/repo` is where the tracker's issues live;
- PRs on its timeline (`cross-referenced` and `connected` events, with `tracker.kind: github`).

For every other child that isn't `tracker.statuses.wont_do`, find its PRs the same ways with `--state all` instead of `--state merged`, and note its status. Judge it by its PRs, not only its status: when every PR found has merged, it's built, and step 3 dates it like the others; when one is still open, it's still being built; with no PR and its status still the first one, its work never started. Step 2 needs this.

Keep only merged PRs. Each one's change reaches the repo's default branch through its **landing PR**: the PR itself, when it merged into the default branch, or, for a PR merged into another branch (on a stack, into the PR below it), the PR that later brought that branch onto the default branch. Its merge commit is the **landing commit**. Step 3's script finds both for you; when the user gave you the PRs' merges instead, find them by the same rule: follow each PR from the base branch that merged after it and either was open when it merged into that branch or has a head that holds it, down the stack, and the first of them to merge into the default branch lands it. A PR from a reused branch name (opened later, for other work) doesn't. When the evidence doesn't say when such a PR was opened or what its head holds, a PR from that branch that merged into the default branch after it, to bring the branch up to date or to land it, carries it. A PR the user says merged, without saying which branch, merged into the default branch unless something they gave says otherwise (its base, or a branch it was stacked on); the script checks this for itself when it runs. A PR whose change hasn't reached the default branch yet hasn't shipped: list it in the checks. Such a child with no merged PR found goes in the checks ("no merged PR found for PROJ-1234"); don't treat it as not built.

## 2. What shipped

The note describes what the merged PRs built, read from the children and their PRs, not from EPIC's plan or description. A child closed as `tracker.statuses.wont_do`, or one whose work never started, is left out of the note entirely (not "coming soon", not "planned"), and listed in the checks as planned but not built, for the user to confirm. A child the feature needs that's still being built (an open PR, or its work started and it's at neither `tracker.statuses.done` nor `tracker.statuses.ready_for_release`) isn't left out: the feature isn't finished, so its note is held (step 4).

## 3. When customers could use it

For each repo the feature touched, find the date production first carried that repo's **last** change for the feature, the way the repo's `production` key says. "Last" means the last to land on the default branch, by its landing PR's merge (step 1), not by the PR's own merge: a stacked PR that merged early but landed late can be the last change.

**Run the script** in this skill's folder, once per repo, with the repo's `production` and every merged PR the feature has in that repo:

```
python3 <this skill's folder>/scripts/production_date.py --repo <owner/name> --workflow <file> <PR> [<PR>…]
```

Use `--workflow <file>` for `{ workflow: <file> }`, `--release` for `release`, `--merge` for `merge`, and none of the three when the repo has no `production`. It reads GitHub with `gh`, finds each PR's landing PR, takes the last to land, and prints one JSON object. Use what it prints as it is: don't redo its search by hand, and don't move its date.

| `status` | What it means |
|---|---|
| `dated` | `date` (UTC) is when production first carried the repo's last change; `deploy` says what carried it. |
| `held` | Production hasn't carried it yet: no deploy or release contains it, or a PR hasn't reached the default branch (its `prs` entry has `landed: false`). The note is held (step 4); `reason` says what it waits for. |
| `not_found` | **Date not found.** Put "Date not found: <`reason`>" in the checks, and the feature's date is `[date]`. When the reason is that the repo has no `production`, also give the evidence you have (`last_change`: its last change and when it landed), and ask how the repo reaches production, or suggest setting its `production` key. |

If the script exits with an error, or prints something that isn't its JSON, or `python3` or `gh` isn't there, the date isn't found: say why in the checks. Don't work the date out by hand from `gh` instead.

**Evidence the user gave counts as read** (see the top of this skill): when the user has told you which deploy, release or merge carried a repo's last change, use that for the repo, and don't run the script for it. Don't add checks saying you didn't run the script, compare commits, or see a run's ID or end time for what they told you; in the evidence table, its "Matched by" is "as you gave it".

**What the script does,** so you can explain its result, and apply the same rules to evidence the user gave:

| `production` | The date of a change |
|---|---|
| `{ workflow: <file> }` | When the first run of that workflow to **succeed**, on the default branch or a tag (not a pull request), whose head commit contains the landing commit, finished: its first successful attempt's end, not when it started (a run can cross midnight, or succeed only on a re-run). A run on a tag counts only if it ran the tag's own commit. It searches every run from the day **before** the change landed to today, page by page, narrowing its window when GitHub's 1,000-run limit for one search would hide some. If the workflow has deployed before and no run up to today contains the change, it's `held`; if it has never succeeded, or its file isn't found, `not_found`. |
| `release` | The publish date of the first published release, by publish date (drafts and pre-releases skipped), whose tag contains the landing commit, from every release published from the day **before** it landed. None: `held`. |
| `merge` | When the landing PR merged. Not a commit's date, which can be when the code was written. |
| *(missing)* | `not_found`. Don't guess, and don't assume it deploys on merge. |

A deploy or release matches by commit (GitHub's `compare` says the run or tag is `ahead` of the landing commit, or `identical`), never by a date near it; only a stacked PR's landing PR is found by dates (step 1), since a rebase rewrites the stack's commits. It never returns a nearby date: anything it can't read, or a search GitHub won't list in full, is `not_found` with the reason.

**One note per feature.** Most epics ship one feature and get one note. An epic that shipped separate features, each usable without the other, gets one note for each, dated and evidenced on its own from the changes that feature needed. A feature's date is the **latest** of its repos' dates: customers can use it only when every part is live. Every date rule works this way, here and in step 4: when more than one thing must happen first (each repo's deploy, a flag going on for everyone, a correction's run), the date is the latest of them. If any repo's date wasn't found, the feature's date is `[date]`.

**Never use the tracker's resolution date,** or the date a ticket moved to done: an epic can close weeks before or after customers could use it.

Show each feature's evidence in one table, one row per repo, from the script's `last_change` and `deploy` (or from what the user gave): which run, release or merge carried it, its commit, and how it was matched. Write anything you'd add about the dates in the checks, not between the table and the checks.

| Repo | Last change | Deploy | Matched by | Date |
|---|---|---|---|---|
| api | org/api#120, landed June 9 | `release-prod.yml` run 4211 on `main`, at `9f2c1ab` | contains `4e1d2c0`, #120's merge (`compare`: ahead) | June 11, 2026 |
| web | org/web#45, landed June 10 with #44 | merge of #44 (deploys on merge) | #44's merge | June 10, 2026 |

## 4. Can customers use it yet?

Code in production isn't always something customers can use. For each feature, hold its note when any of these is true:

- **A feature flag.** Read each merged PR's diff and, on the default branch, the code that renders or routes to what it adds (the page, the menu entry, the route, the handler), for a feature flag: a check that keeps the feature off for some or all customers until it's rolled out. A circuit breaker or kill switch, a check that turns a working feature off when something goes wrong, isn't a feature flag and doesn't hold the note. When the code doesn't make clear which one a check is, don't guess, and don't decide from its default value alone: hold the note as for a flag, with "[Held: is `<check>` a feature flag or a circuit breaker? Ask the developer before publishing.]", and put the same question in the checks. Feature flags can come from any library or the team's own helper: `flags.isEnabled("spend-by-team")`, `useFeature("bulk-export")`, `if (featureFlags.newBilling)`, `variation("usage-alerts", false)`. Never read a flag provider: you can't know who has the flag on, so say "check the flag's rollout", and never say the rollout was checked. If the user tells you the flag is on for everyone, that counts: don't hold the note for it, and count the flag going on for everyone as one more thing that had to happen first (step 3's rule), or use `[date]` if they didn't say when.
- **A slice that isn't live yet.** A child the feature needs that's still being built (step 2), named by its key and status; or one whose PR hasn't landed on the default branch yet (step 1: merged into a stacked branch that hasn't merged), or whose landing commit no production deploy has carried yet, by step 3's rule: for example one at `tracker.statuses.ready_for_release` whose PR landed after the last deploy.
- **A correction to past data that hasn't run.** A job, backfill, script or data migration a merged PR adds for someone to run by hand, with no record that it ran in production (a comment, a run, a runbook record), when the note's promise depends on it ("past costs are corrected"). Once it has run, count its recorded run as one more thing that had to happen first (step 3's rule).

A held note is still drafted in full. Its date is `[date]`, the day it's live for everyone, and one line in square brackets directly under the date line (under the title, when the voice has no date line) says it's held and names each thing it waits for: "[Held: waiting for the `spend-by-team` flag to be on for everyone. Check the flag's rollout.]" Like `[date]` and `[N]`, the brackets mark it as the user's to remove before publishing; it never reaches customers. Its evidence table row dates are what you found so far, and the feature's date is `[date]`. Write it to be true on the day it's published, without claiming that anything it waits for has already happened: not "past costs already include the correction" while the recalculation hasn't run, but "past costs are recalculated the same way".

## 5. Already announced?

Check the team's published notes, so nothing is announced twice. Fetch `release_notes.published_url`, or use the page's text if the user gave it: pasted text counts as fetched. Compare each feature with the posts by what it does for the customer, not by title: a post called "Spend Alerts by Email" announces a feature called "Know right away when spending jumps".

When a post already covers a feature, don't present its note as new. Still give the note, so the reply keeps its shape, with "[Already announced: <post title>, <date>]" on its own line under the date line, or under the title when the voice has no date line (under the held line, if it has one), for the user to decide, and name the post in the checks. When a post covers only part of it (a beta, one slice), the note is new: write about what's new since that post, and name the post in the checks.

If the page shows only the newest posts (one page of a longer changelog), check what it shows, and say in the checks how far back it goes.

When you have neither the page's text from the user nor a readable `release_notes.published_url` (it isn't set, or there's no web tool, an error, a sign-in page), never say a feature wasn't announced before. Say "Repeat check not done: <why>." in the checks, and add "check it isn't already announced" for each note.

## 6. The voice

**The team's voice.** When the config sets `release_notes.voice`, read that file, its path relative to the folder the config file really lives in (when the config is a link, follow it: `realpath`). It's the team's whole voice: follow only its rules, don't read `references/fallback-voice.md`, and add nothing from it, even where the team's file says nothing (no sign-off rule means no sign-off, not roost's).

**roost's fallback voice.** Follow `references/fallback-voice.md` only when the team's voice isn't available, and say why in the checks, in one line:
- `release_notes.voice` isn't set: "Used roost's fallback voice: the config has no `release_notes.voice`."
- The file can't be read: "Couldn't read the voice file `<path>`: used roost's fallback voice."

Before you send the note, check it against every rule in the voice you're using, one by one, and add none of your own. With roost's fallback voice, the ones most often missed: keep the title well inside the voice's word limit, aiming for 3 to 5 words, and count every word, numbers and short words included ("Invoices Searchable Up to 90 Days Back" is 7 words; "Search Older Invoices" is 3); put the practical number or timing the evidence gives (how soon, how many) in the closing line, not only in the body; and say what the customer doesn't have to do when the evidence says it, in the body, before the closing line, so the closing line stays last.

## 7. Write the reply

**Facts the evidence doesn't give** (a number, a limit, a price, a plan's allowance) go in as `[N]`, never guessed. Leaving a fact out is fine when the note reads well without it.

The reply is these, in this order, and nothing else. It starts with the note itself: no introduction before it. Anything you'd want to say about the note (why this date, what you assumed) goes in the checks.

1. **The note,** complete and ready to paste, with nothing interrupting it: its title, the line with its category and date (or wherever the voice puts the date, if anywhere), the bracketed held and already-announced lines if it has them (steps 4 and 5), the body, then the closing line, sign-off and byline the voice has. One version of each note, never alternatives.
2. **The evidence table** (step 3). It may come before the note instead.
3. **Checks:** one short list, each item one line:
   - every `[N]` and `[date]` in the note, and what would fill it;
   - what was planned but not built, and done children with no merged PR found;
   - every date not found, and every source that couldn't be read (deploy runs, releases, the tracker), with the script's `reason` for each repo it didn't date;
   - each held note and what it waits for, with "check the flag's rollout" for a flag (step 4);
   - each feature already announced, naming the post's title and date, or "Repeat check not done: <why>." and "check it isn't already announced" for each note (step 5);
   - the voice line, when roost's fallback voice was used (step 6).

For an epic that shipped separate features, give 1 and 2 for each feature in turn, then one list of checks for them all. A catch-up's reply is laid out at its end.

## Catch-up since a date

When the user asks for everything released since a date ("catch us up since our last post on February 1"), call that date SINCE. Each note in a catch-up is built and checked exactly as an epic's is (steps 1 to 7): one note per feature, dated through `production_date.py`, held when customers can't use it yet, checked against the published notes, in the team's voice.

1. **Find what moved.** This skill's script runs the tracker's search for tickets moved to `tracker.statuses.done` or `tracker.statuses.ready_for_release` since SINCE, reads every page, and sorts what it finds:
   - **Jira:** `python3 <this skill's folder>/scripts/catch_up.py jira --site <tracker.jira.site> --project <tracker.jira.project> --since SINCE --done "<tracker.statuses.done>" --ready "<tracker.statuses.ready_for_release>"`. It uses `JIRA_EMAIL` and `JIRA_API_TOKEN` from the environment. When they aren't set (it exits 2 and says so), stop and tell the user to set both (a token comes from https://id.atlassian.com/manage-profile/security/api-tokens), then run it again. Never search through the Atlassian MCP or the browser instead, and never copy search results into files for it.
   - **GitHub:** `python3 <this skill's folder>/scripts/catch_up.py github --repo <tracker.github.repo> --since SINCE --ready-label "<tracker.statuses.ready_for_release>"`

   It prints `epics`, `candidates` (standalone stories, tasks and bugs), `children` (slices that count toward their epic) and `dropped` (Tests, sub-tasks, whose work is their parent's, and tickets that have moved back out of done), each with a reason, `notes` (lines for the checks about tickets kept on less than full evidence), and `complete: false` with a `reason` when the search wasn't read in full. When the user gives you the tickets instead, sort them by the same rules yourself.
2. **Each epic.** Run steps 1 to 6 for each epic in `epics`.
3. **The cut-off.** A ticket resolved after SINCE can have reached customers before it. Give every feature's date to `python3 <this skill's folder>/scripts/catch_up.py cutoff --since SINCE`, as `[{"key": …, "status": …, "date": …}]` on stdin, from each feature's `production_date.py` result. SINCE is a UTC day, like every date the scripts print. It drops each feature live before SINCE, with the reason, and sorts the rest oldest first, held ones last. When you can't run it, apply the same rule: compare production dates, never resolution dates.
4. **Candidates.** List every standalone story, task and bug, one line each: its key, its title and what changed for customers, for the user to pick. Draft none of them. Name only candidates there: a dropped ticket goes in the checks, never in the candidates, and with none, the list says "No candidates." A candidate the user picks gets steps 1 to 7, like an epic, dated by its own production.
5. **The reply,** in this order and nothing else:
   1. every note, complete, oldest first, one after another with nothing between them, rotating the voice's sign-offs as it says;
   2. the evidence tables, in the same order;
   3. the candidates;
   4. one list of checks for them all (step 7's), plus each ticket dropped as moved back out of done, each feature live before SINCE and its date, the script's `notes`, and a search that wasn't read in full (its `reason`).

