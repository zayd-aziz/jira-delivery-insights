import secrets

from fastapi import Depends, Security
from fastapi.security import APIKeyHeader
import os

import anthropic
from fastapi import FastAPI, HTTPException

from fetch import JiraError, fetch_all_issues, get_config
from report import build_insights, generate_report

app = FastAPI(title="Jira Delivery Insights")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided_key: str = Security(api_key_header)):
    expected_key = os.getenv("API_KEY")
    if not expected_key:
        raise HTTPException(status_code=500, detail="Missing API_KEY on server")
    if not provided_key or not secrets.compare_digest(provided_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

def load_live_issues():
    try:
        config = get_config()
    except JiraError as error:
        raise HTTPException(status_code=500, detail=str(error))

    try:
        return fetch_all_issues(config)
    except JiraError as error:
        raise HTTPException(status_code=502, detail=str(error))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/insights")
def insights(_: None = Depends(require_api_key)):
    return build_insights(load_live_issues())

@app.get("/report")
def report(_: None = Depends(require_api_key)):
    metrics = build_insights(load_live_issues())

    if not os.getenv("ANTHROPIC_API_KEY"):
        raise HTTPException(status_code=500, detail="Missing ANTHROPIC_API_KEY")

    try:
        text = generate_report(metrics)
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Anthropic authentication failed — check ANTHROPIC_API_KEY")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=503, detail="Rate limited by the Anthropic API — try again shortly")
    except anthropic.APIConnectionError:
        raise HTTPException(status_code=502, detail="Could not reach the Anthropic API")
    except anthropic.APIStatusError as error:
        raise HTTPException(status_code=502, detail=f"Anthropic API error {error.status_code}")

    if not text.strip():
        raise HTTPException(status_code=502, detail="Claude returned no report text")

    return {"report": text, "insights": metrics}

@app.get("/")
def root():
    return {
        "name": "Jira Delivery Insights",
        "status": "running",
        "docs": "/docs"
    }
