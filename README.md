# Jira Delivery Insights

A small service that pulls delivery data out of Jira Cloud, turns it into
structured metrics, and uses Claude to generate a plain-English delivery
report — deployed as a containerized API.

**Live service:** https://jira-delivery-insights.onrender.com

## What it does

1. **Fetches** issues from a Jira Cloud project via the REST API (`/rest/api/3/search/jql`), handling cursor-based pagination.
2. **Analyzes** those issues into delivery metrics: counts by status category, open issues by assignee, and the age of open issues.
3. **Reports** on those metrics using the Anthropic API, turning raw numbers into a short written summary.
4. **Serves** all of the above over HTTP as a small FastAPI service, protected by an API key.

## Endpoints

| Method | Path        | Auth required | Description                                      |
|--------|-------------|----------------|---------------------------------------------------|
| GET    | `/health`   | No             | Basic liveness check                              |
| GET    | `/insights` | Yes            | Returns computed delivery metrics as JSON          |
| GET    | `/report`   | Yes            | Returns metrics plus a Claude-generated summary    |

Protected endpoints require an `X-API-Key` header matching the server's `API_KEY` environment variable.

## Project layout

- `fetch.py` — Jira API client: authentication, pagination, error handling
- `insights.py` — turns raw Jira issues into delivery metrics
- `report.py` — calls the Anthropic API to
