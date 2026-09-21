## Pagination and JSON output

### Cursor-based pagination
- Jira's /search/jql returns a `nextPageToken` with each page. I pass it
  back in the next request's params to get the following page.
- The token is opaque: I never parse or build it, just hand it back.
- Loop pattern: `while True`, break when no token comes back.
- Use `data.get("nextPageToken")`, not `data["nextPageToken"]`. The key is
  missing on the last page, and `.get()` returns None instead of crashing.

### Why trust the token instead of doing page math
- With 15 issues at 5 per page, Jira still gave me a token after page 3.
  The 4th request returned 0 issues and no token. If I'd calculated
  "3 pages" myself I'd have been fine here, but the server is the only
  one that really knows when it's done.
- Cursor vs offset: with offset paging (`startAt`), if data changes
  mid-fetch, results shift and you can get duplicates or skip items.
  Cursors avoid that.

### Bugs I hit
- Wrote `params["nextPageToken"]` without `= next_token`. It only reads
  the value. Would have raised KeyError on page 2.
- The bug was invisible with maxResults=20 because everything fit on one
  page. Lesson: test pagination with a small page size to force
  multiple pages.

### Writing JSON to disk
- `json.dump(obj, f)` writes to a file; `json.dumps(obj)` returns a string.
- `os.makedirs("output", exist_ok=True)` because `open()` won't create
  folders.
- `extend` adds items from a list; `append` would nest the whole list.
- `output/` is gitignored: real Jira data never goes in the repo. Added
  the ignore line BEFORE the first run.
- JSON `null` becomes Python `None` (e.g. unassigned issues). Code that
  reads assignee needs to handle that.