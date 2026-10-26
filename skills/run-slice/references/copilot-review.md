# Copilot review of a slice's PRs

Send this to each session that owns one of the slice's PRs, word for word, with the PR numbers filled in. The session does the work; you read its report.

---

**run-slice: Copilot review for <STORY>, PRs #<n>[, #<n>]**

Copilot's review depth is a repo default, so request it with no options.

1. **Request it** on each PR as soon as it's pushed. Don't wait for CI; the review and the checks run in parallel: `gh pr edit <n> --add-reviewer @copilot`. Note the time.
2. **Wait for the review.** Poll every 2 minutes, for up to 30 minutes:
   `gh api --paginate repos/<owner>/<repo>/pulls/<n>/reviews --jq '.[] | select(.user.login == "copilot-pull-request-reviewer[bot]") | .submitted_at' | sort | tail -1`
   (`--paginate` reads every page; the endpoint returns 30 reviews per page). It's done when that time is after your request. If 30 minutes pass with nothing, say so in the report and stop.
3. **Read every open thread** Copilot left:
   ```
   gh api graphql --paginate -f query='query($o:String!,$r:String!,$n:Int!,$endCursor:String){repository(owner:$o,name:$r){pullRequest(number:$n){reviewThreads(first:100,after:$endCursor){pageInfo{hasNextPage endCursor} nodes{id isResolved comments(first:20){nodes{databaseId author{login} path line body}}}}}}}' -f o=<owner> -f r=<repo> -F n=<n> \
     --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved | not) | select(.comments.nodes[0].author.login == "copilot-pull-request-reviewer")'
   ```
   `--paginate` follows `endCursor` through every page, so no thread is missed. Each line of output is one open Copilot thread.
4. **Judge each one against the code**, not the comment's wording, with the slice's fix-now rule:
   - **Accept:** it's real, and this slice introduced it or it stands in the way of the story's or epic's goal. Fix it test-first (a test that fails first, then the fix), one commit (signed, if the team signs commits), pushed. Reply on the thread with the commit and the test, then resolve the thread.
   - **Decline:** it's wrong, already handled, or not worth changing. Reply with why, citing the file:line that shows it. Leave the thread open.
   - **Older:** it's real but in code this slice didn't change, and it doesn't block the goal. Reply that it's older and is being ticketed. Leave the thread open; the orchestrator files the ticket.

   Reply with `gh api repos/<owner>/<repo>/pulls/<n>/comments/<databaseId>/replies -f body='…'`, and resolve with `gh api graphql -f query='mutation($t:ID!){resolveReviewThread(input:{threadId:$t}){thread{isResolved}}}' -f t=<thread id>`.
5. **After any fix,** re-run the affected suites and wait for CI on the new head. Don't request a second Copilot review; the orchestrator's review of the fixes covers them.

Reply to the orchestrator, as the last thing you do, with one table: # / PR / thread (link) / what Copilot said, in a few words / **accepted**, **declined** or **older** / why, with file:line / fix commit and test, if accepted. Then **CI** (each PR's newest completed result) and **Needs from the user**.
