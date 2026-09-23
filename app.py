from fastapi import FastAPI, HTTPException

from fetch import JiraError, fetch_all_issues, get_config
from report import build_insights

app = FastAPI(title="Jira Delivery Insights")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/insights")
def insights():
    try:
        config = get_config()
    except JiraError as error:
        raise HTTPException(status_code=500, detail=str(error))

    try:
        issues = fetch_all_issues(config)
    except JiraError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return build_insights(issues)
