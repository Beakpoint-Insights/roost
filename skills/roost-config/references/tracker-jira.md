# Tracker adapter: Jira

How to do each tracker operation when `tracker.kind` is `jira`. The skills say *what* to do ("set the parent", "edit the Carry-over comment in place"); this file says *how*. Use `tracker.jira.cloud_id` and `tracker.jira.project` from the config.

Most operations go through the Atlassian MCP tools. A few can't: they go through Jira's REST API, with the user's API token when `JIRA_EMAIL` and `JIRA_API_TOKEN` are set (see "REST with an API token"), and otherwise from the user's signed-in Jira session in the Playwright browser (see "Fallback: REST from the browser").

## Words

| Skills say | In Jira |
|---|---|
| Epic, story, bug, task, sub-task | Issue types of the same names |
| Parent | The `parent` field |
| Components | The `components` field. Set them on every ticket you create when `tracker.components_required` is true: copy them from the story, or from the epic for epic-level work. An epic and its stories get theirs chosen from the project's list when they're created (`shape-epic` phases 2 and 4) |
| A status (`tracker.statuses.*`) | A workflow status, reached by a transition |
| "relates to" link | Link type "Relates" |
| A ticket's tests | Links of type `tests.xray.test_link_type` (the test is inward, the story outward) |

## Operations

| Operation | How |
|---|---|
| **Who am I** | `atlassianUserInfo` gives the account ID of the person running the session. Use it to assign work to them; never hard-code an account. |
| **Read a ticket** | `getJiraIssue`, with `comment` in `expand` or `fields` when you need comments. |
| **Search** | `searchJiraIssuesUsingJql`. Common queries below. |
| **Create** | `createJiraIssue` with `projectIdOrKey`, `issueTypeName`, `summary`, `description`, and `parent` set at creation. Set Components right after with `editJiraIssue` if the create call didn't take them. |
| **List components** | REST (below): `GET /rest/api/3/project/<tracker.jira.project>/components` gives each component's `id`, `name` and `description`. Use it to choose Components for a new ticket. |
| **Description format** | Descriptions are ADF (Atlassian Document Format). Use `h2` headings, tables and numbered lists so they read well in Jira. |
| **Edit fields** | `editJiraIssue`. **`fields.labels` replaces every label,** so always send the existing labels plus the new ones. |
| **Set or clear a parent** | **Not through `editJiraIssue`, which silently ignores parent changes.** Use REST (below): `PUT /rest/api/3/issue/<key>` with `{"fields":{"parent":{"key":"<EPIC>"}}}`, or `{"fields":{"parent":null}}` to clear it. Read the ticket back afterwards. |
| **Assign and start** | `editJiraIssue` with the assignee's account ID, then `getTransitionsForJiraIssue` and `transitionJiraIssue` to `tracker.statuses.in_progress`. |
| **Move to a status** | `getTransitionsForJiraIssue`, then `transitionJiraIssue` with the transition to the status the config names. Read the status back. |
| **Comment** | `addCommentToJiraIssue`. |
| **Edit a comment in place** | **Not through the MCP, which can't edit comments.** Use REST (below): `PUT /rest/api/3/issue/<key>/comment/<id>` with the whole new body in ADF. Keep the comment's ID in your state file; find it again by its heading if you lose it. Read it back afterwards. |
| **Link two tickets** | `createIssueLink` with the link type's name, `inwardIssue` and `outwardIssue`. Read one side back to check. |
| **Attach a file** | **The MCP can't upload.** Use REST (below): `POST /rest/api/3/issue/<key>/attachments`. Read the ticket's attachments back and compare the size. |
| **Read an attachment** | REST (below): `GET /rest/api/3/issue/<key>?fields=attachment`, then fetch the attachment's `content` URL with the same authentication. |
| **Fix version** | `editJiraIssue` with `fixVersions`, using a version that already exists in the project. |

## Common searches

- Open children of an epic, at any depth: `parent = <EPIC> AND statusCategory != Done`, then the same for each child's sub-tasks.
- Open and not waiting to ship: add `AND status != "<tracker.statuses.ready_for_release>"`.
- Linked open tickets: `issue in linkedIssues(<KEY>) AND statusCategory != Done`.
- Created during a window: `project = <project> AND created >= "<start>" AND (parent = <EPIC> OR text ~ "<KEY>")`.
- Roadmap epics: `project = <project> AND type = Epic AND labels = roadmap AND statusCategory != Done ORDER BY created ASC`.

`statusCategory != Done` treats Cancelled, Won't Do and other closed statuses as closed.

## REST with an API token

The usual way, with no browser: it works with several sessions at once and on a machine with no screen. It needs `JIRA_EMAIL` (the user's Atlassian email) and `JIRA_API_TOKEN` (an API token from https://id.atlassian.com/manage-profile/security/api-tokens) in the environment. **Never print the token**, never put it in a command's text, and never write it to a file; pass it only through `-u "$JIRA_EMAIL:$JIRA_API_TOKEN"`.

```bash
J="https://<tracker.jira.site>/rest/api/3"
AUTH=(-u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H 'Accept: application/json')

# Set (or clear, with null) a parent
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" -X PUT -H 'Content-Type: application/json' \
  "$J/issue/PROJ-1234" -d '{"fields":{"parent":{"key":"PROJ-1200"}}}'

# Replace a comment's body (ADF)
curl -s -o /dev/null -w '%{http_code}\n' "${AUTH[@]}" -X PUT -H 'Content-Type: application/json' \
  "$J/issue/PROJ-1234/comment/<id>" -d @comment.json

# Upload an attachment
curl -s "${AUTH[@]}" -X POST -H 'X-Atlassian-Token: no-check' \
  -F "file=@PROJ-1234 Build Guide.html" "$J/issue/PROJ-1234/attachments"

# Download an attachment (its URL from ?fields=attachment)
curl -sL "${AUTH[@]}" -o "<file>" "<attachment content URL>"
```

Check each call's status code (200 or 204), then read the result back through the MCP or `GET`. A 401 means the token or email is wrong or expired: tell the user, and don't fall back silently. Write a large ADF body to a file in your scratch folder and pass it with `-d @file`, rather than putting it on the command line.

## Fallback: REST from the browser

Only when `JIRA_API_TOKEN` isn't set. Say so to the user once, and suggest setting the token: the browser is shared by every session, and only one can use it at a time (see "The signed-in browser" in `roost-config`).

Use the user's signed-in Jira session in the Playwright browser. If they aren't signed in, open `https://<tracker.jira.site>` and wait for them.

**JSON calls** (parent changes, comment edits): go to any page on the site, then call `fetch('/rest/api/3/…', { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: … })` from inside the page with `page.evaluate`, and read the status code back.

**Uploading an attachment:**

1. Write a script into `.playwright-mcp/` that holds the file as base64. Playwright's `run_code` has no `fs` or dynamic `import`.
2. Have the script go to the ticket's page, then call `fetch('/rest/api/3/issue/<KEY>/attachments')` **from inside the page** with `page.evaluate`, sending a `FormData` body and the header `X-Atlassian-Token: no-check`.
3. Run it with `browser_run_code_unsafe` and the `filename` parameter.

Don't use `page.request.post`; Jira rejects it with "XSRF check failed". A large file makes the tool echo the whole script, so read just the `### Result` line from the saved output.

**Screenshots as evidence:** `gh` can't attach images to a PR, so put screenshots on the story's Jira issue ("Attach a file" above) and link the story from the PR.
