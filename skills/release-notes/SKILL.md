---
name: release-notes
description: Draft customer-facing release notes for an epic that has shipped, ready to paste. Dates each note by when customers could first use the feature (the production deploy, release or merge that first carried its last change, shown in an evidence table), never by the tracker's resolution date; writes only what the slices built, listing anything cut; leaves facts the evidence doesn't give as [N]; and follows roost's fallback voice. Never publishes or posts anything. Use when the user says "draft the release note for PROJ-X", "write the release notes for this epic", "what do we tell customers about PROJ-X", and from close-out-epic once production runs the epic.
---

# Release Notes

A release note is public, and hard to take back once it's out. Each one has to be dated by when customers could actually use the feature, describe what was built (not what was planned), and leave anything the evidence doesn't say for the user to fill in. This skill gathers that evidence and drafts the note; the user publishes it.

**First, load the team config with `roost-config`,** and read its tracker adapter.

**Input:** the epic's key. Everything below calls it EPIC.

**Evidence the user gives counts.** When the user has already given you facts (the tickets, the PRs, the deploy runs, a page's text), use them as read, and don't look them up again. Look up only what's missing. Whatever you couldn't read, from the user or the tools, goes in the checks (step 7), named.

**Never publish or post anything:** no tracker comments, no status changes, no posts. The reply is the draft.

## 1. Find the work

Read EPIC and its children (stories, tasks, bugs) through the tracker adapter, with their statuses. For each child that's at `tracker.statuses.done` or `tracker.statuses.ready_for_release` (a shipped ticket can still sit there), find the PRs that built it, in every repo in `repos`:

- the PRs that close it (a closing reference);
- PRs whose title, body or branch name has its key (`gh pr list -R <repo> --state merged --search "<key> in:title,body"`, and `head:<branch>` for `vcs.branch_name`'s form of the key);
- PRs on its timeline (`cross-referenced` and `connected` events, with `tracker.kind: github`).

Keep only merged PRs, with each one's merge commit and merge date. Such a child with no merged PR found goes in the checks ("no merged PR found for PROJ-1234"); don't treat it as not built.

## 2. What shipped

The note describes what the merged PRs built, read from the children and their PRs, not from EPIC's plan or description. A child closed as `tracker.statuses.wont_do`, or one with no merged work, is left out of the note entirely (not "coming soon", not "planned"), and listed in the checks as planned but not built, for the user to confirm.

## 3. When customers could use it

For each repo the feature touched, find the date production first carried that repo's **last** change for the feature, the way the repo's `production` key says:

| `production` | The date of a change |
|---|---|
| `{ workflow: <file> }` | The first run of that workflow that **succeeded**, ran on the default branch or a tag (not a pull request), and whose head commit contains the PR's merge commit. List runs from the day **before** the merge (`--created` compares UTC dates): `gh run list -R <repo> --workflow <file> --status success --limit 1000 --created "<day before merge>..<end>" --json databaseId,headSha,headBranch,event,createdAt`. `gh` returns the newest first and `--limit` drops the oldest, so if it returns exactly the limit, the first deploy may be missing: move `<end>` earlier until it returns fewer. Then, oldest first, check each candidate with `gh api repos/<repo>/compare/<merge sha>...<run head sha> --jq .status`: `ahead` or `identical` means the run contains it. Match by commit, never by date. If no run contains it, or `gh` can't read the runs, say so in the checks; don't fall back to a nearby date. |
| `release` | The `publishedAt` of the first published release whose tag contains the merge commit: `gh release list -R <repo> --exclude-drafts --exclude-pre-releases --order asc --limit 1000 --json tagName,publishedAt`, checked oldest first with `compare` the same way. If it returns exactly the limit, say so in the checks. |
| `merge` | The merge date. |
| *(missing)* | **Date not found.** Don't guess, and don't assume it deploys on merge. Say "Date not found: `<repo>` has no `production` in the config", give the evidence you do have (its last change and when it merged), and ask how the repo reaches production, or suggest setting its `production` key. |

The feature's date is the **latest** of its repos' dates: customers can use it only when every part is live. If any repo's date wasn't found, the feature's date is `[date]`.

**Never use the tracker's resolution date,** or the date a ticket moved to done: an epic can close weeks before or after customers could use it.

Show the evidence in one table, one row per repo:

| Repo | Last change | Deploy | Date |
|---|---|---|---|
| api | org/api#120, merged June 9 | `release-prod.yml` run on June 11 | June 11, 2026 |
| web | org/web#45, merged June 10 | deploys on merge | June 10, 2026 |

## 4. Can customers use it yet?

Not checked yet: this version doesn't look for feature flags, slices waiting to deploy, or corrections to past data that haven't run. Say so in the checks.

## 5. Already announced?

Not checked yet: this version doesn't read the team's published notes. Say so in the checks.

## 6. The voice

Follow `references/fallback-voice.md`, roost's own voice, and say in the checks, in one line, that the fallback voice was used because the config has no `release_notes.voice`.

Before you send the note, check it against every rule in the voice, one by one. The ones most often missed: keep the title well inside the voice's word limit, aiming for 3 to 5 words, and count every word, numbers and short words included ("Invoices Searchable Up to 90 Days Back" is 7 words; "Search Older Invoices" is 3); put the practical number or timing the evidence gives (how soon, how many) in the closing line, not only in the body; and say what the customer doesn't have to do when the evidence says it.

## 7. Write the reply

**Facts the evidence doesn't give** (a number, a limit, a price, a plan's allowance) go in as `[N]`, never guessed. Leaving a fact out is fine when the note reads well without it.

The reply is these, in this order, and nothing else. It starts with the note itself: no introduction before it. Anything you'd want to say about the note (why this date, what you assumed) goes in the checks.

1. **The note,** complete and ready to paste, with nothing interrupting it: its title, the line with its category and date, the body, and the closing line. One version only.
2. **The evidence table** (step 3). It may come before the note instead.
3. **Checks:** one short list, each item one line:
   - every `[N]` and `[date]` in the note, and what would fill it;
   - what was planned but not built, and done children with no merged PR found;
   - every date not found, and every source that couldn't be read (deploy runs, releases, the tracker);
   - "Not checked yet: feature flags, unreleased slices and already-published notes." (steps 4 and 5);
   - the voice line (step 6).
