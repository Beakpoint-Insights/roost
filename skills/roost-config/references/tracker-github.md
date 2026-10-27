# Tracker adapter: GitHub Issues

How to do each tracker operation when `tracker.kind` is `github`. The skills say *what* to do ("set the parent", "edit the Carry-over comment in place"); this file says *how*, with the `gh` CLI. Issues live in `tracker.github.repo` (`owner/repo`).

## Keys

- **A key** is the issue number, written `#123` in text, comments and commit messages (GitHub links it), and `owner/repo#123` when it's in another repo. The skills' `PROJ-1234` examples stand for it.
- **A key in a name** (a branch, a tag on an eval case, a state file) is written `issue-123`, since `#` isn't safe there: branch `issue-123-short-description` (`vcs.branch_name`'s `{key}`), state file `issue-123.md`.

## In a prompt

A prompt that must stand alone (the tech lead prompt) introduces the tracker as: "Its tracker is GitHub Issues in `<tracker.github.repo>`. A file attached to an issue is a gist linked from one of its comments."

## Words

| Skills say | In GitHub Issues |
|---|---|
| Epic, story, task, bug | An issue. Its kind is its issue type when `tracker.github.issue_types` is true (the organisation's Epic, Story, Task and Bug types); otherwise a label: `epic`, `story`, `task`, `bug` |
| Sub-task | A sub-issue of the task |
| Parent | Sub-issues: a story is a sub-issue of its epic, a test or bug of its story or epic |
| Components | Labels named `<tracker.github.component_prefix><name>` (default prefix `component: `). Set them on every issue you create when `tracker.components_required` is true |
| A status (`tracker.statuses.*`) | `todo`: open, with no status label. `done`: closed as completed. `wont_do`: closed as not planned. Any other (`in_progress`, `ready_for_release`): open, with a label named exactly the status's name, and no other status label |
| "relates to" link | A comment that mentions the other issue ("Relates to #123"); GitHub records it on both |
| Labels | Labels |
| Fix version | A milestone |
| Description format | Markdown, not ADF |
| Attachment | A secret gist, linked from a comment on the issue (GitHub's API can't upload files to an issue) |
| A ticket's tests | What the tests adapter says (for `evals`, the cases tagged with its key) |

## Operations

`R` is `tracker.github.repo`.

| Operation | How |
|---|---|
| **Who am I** | `gh api user --jq .login`. Use it to assign; never hard-code a login. |
| **Read a ticket** | `gh issue view <n> -R R --json title,body,state,stateReason,labels,assignees,milestone,comments`. Its parent: `gh api graphql -f query='{repository(owner:"<o>",name:"<r>"){issue(number:<n>){parent{number}}}}'`. Its children, every page: `gh api --paginate repos/R/issues/<n>/sub_issues --jq '.[] \| {number, state, title}'`. |
| **Search** | `gh issue list -R R --state all --limit 1000 --search "<query>" --json number,title,state,labels`. Never trust the default (30 results). If a search returns exactly the limit, there may be more: split it (by date range, say) until each part returns fewer. GitHub's search returns at most 1,000 results, so split any search that could match more. Common searches below. |
| **Create** | `gh issue create -R R --title "…" --body-file <file> --label "<labels>"`, with the kind's label (or, with issue types, set the type right after: `gh api -X PATCH repos/R/issues/<n> -f type=<Type>`), Components labels, and status labels if not `todo`. Then set its parent (below). Create missing labels first: `gh label create "<name>" -R R`. |
| **Edit fields** | `gh issue edit <n> -R R --add-label … --remove-label … --title … --body-file …`. |
| **Set or clear a parent** | Sub-issues take the child's id, not its number: `id=$(gh api repos/R/issues/<child> --jq .id)`, then `gh api -X POST repos/R/issues/<parent>/sub_issues -F sub_issue_id=$id` to set it, or `gh api -X DELETE repos/R/issues/<parent>/sub_issue -F sub_issue_id=$id` to clear it. An issue has one parent: clear the old one before setting a new one. Read it back. |
| **Assign and start** | `gh issue edit <n> -R R --add-assignee @me`, then move it to `tracker.statuses.in_progress` ("Move to a status"), which reopens a closed issue and removes any other status label. |
| **Move to a status** | Reopen it if it's closed and the new status is open (`gh issue reopen <n> -R R`); remove every other status label and add the new one; for `done`, `gh issue close <n> -R R --reason completed`; for `wont_do`, `--reason "not planned"`; to reopen, `gh issue reopen <n> -R R`. Read it back. |
| **Comment** | `gh issue comment <n> -R R --body-file <file>`. |
| **Edit a comment in place** | Find its id: `gh api repos/R/issues/<n>/comments --paginate --jq '.[] \| {id, body: .body[0:80]}'` (keep it in your state file), then `gh api -X PATCH repos/R/issues/comments/<id> -F body=@<file>`. Read it back. |
| **Link two tickets** | A comment on one that mentions the other: `gh issue comment <n> -R R --body "Relates to #<m>"`. |
| **Attach a file** | `gh gist create --desc "<KEY> <file name>" <file>` (secret by default), then a comment on the issue: "Attached: [<file name>](<gist URL>)". Gists hold text only: for a binary file (a screenshot, say), attach `base64 -i <file> -o <file>.b64` instead, named `<file name>.b64`, and say in the comment that it's base64. Never put a secret in a gist: anyone with its link can read it. It needs `gh` signed in with the `gist` scope (`gh auth status`; add it with `gh auth refresh -s gist`). |
| **Read an attachment** | Find the gist link in the issue's comments, then `gh gist view <id> --filename "<file name>" --raw > <file>`. For a `.b64` attachment, decode it: `gh gist view <id> --filename "<file name>.b64" --raw \| base64 -d > <file>`. |
| **Fix version** | `gh issue edit <n> -R R --milestone "<name>"`, using a milestone that already exists. |
| **List components** | `gh label list -R R --search "<tracker.github.component_prefix>" --json name,description`. |

## Common searches

- **Open children of an epic, at any depth:** its sub-issues, every page ("Read a ticket"), then each child's the same way, keeping the open ones.
- **Open and not waiting to ship:** add `-label:"<tracker.statuses.ready_for_release>"` to a search, or drop those with the label.
- **Linked open tickets:** links go both ways, so collect both, then keep only open issues (not PRs), once each:
  - **to it,** from its timeline: `gh api repos/R/issues/<n>/timeline --paginate --jq '.[] | select(.event=="cross-referenced") | select(.source.issue.pull_request == null) | .source.issue.number'`;
  - **from it,** the `#<m>` mentions in its body and comments (`gh issue view <n> -R R --json body,comments`), checking each is an issue, not a PR (`gh issue view <m> -R R --json number` fails for a PR).
- **Created during a window:** `--search "created:>=<start> created:<=<end>"`, then keep those whose parent is the epic or whose text mentions the key.
- **Roadmap epics:** `--search "label:roadmap label:epic state:open sort:created-asc"` (or `type:Epic` with issue types).
- **Moved to a status since a date:** issues closed as completed since then (`--state closed --search "closed:<date>..<today> reason:completed"`), and issues with the `tracker.statuses.ready_for_release` label added since then (`--search 'label:"<ready_for_release>" updated:>=<date>'`, leaving out any closed as not planned, then each one's timeline for when the label was added: `gh api --paginate repos/R/issues/<n>/timeline`, its `labeled` events' `created_at`). `release-notes`' `scripts/catch_up.py github` runs both with `--limit 1000`, splits a search at its limit by date, and sorts the results: epics, standalone candidates, and sub-issues counted toward their parent.

`gh` signs in with the user's GitHub account (`gh auth status`), so nothing here needs a browser or the signed-in Playwright session.
