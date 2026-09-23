from fastapi.testclient import TestClient

import anthropic
import httpx
import app as app_module
from app import app
from fetch import JiraError


client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

FAKE_ISSUES = [
    {
        "key": "TEST-1",
        "fields": {
            "summary": "Open issue",
            "status": {
                "name": "In Progress",
                "statusCategory": {"key": "indeterminate", "name": "In Progress"},
            },
            "assignee": None,
            "created": "2026-09-01T09:00:00.000+0000",
        },
    },
    {
        "key": "TEST-2",
        "fields": {
            "summary": "Done issue",
            "status": {
                "name": "Done",
                "statusCategory": {"key": "done", "name": "Done"},
            },
            "assignee": {"displayName": "Ada"},
            "created": "2026-09-01T09:00:00.000+0000",
        },
    },
]


def test_insights_returns_metrics(monkeypatch):
    monkeypatch.setattr(app_module, "get_config", lambda: {})
    monkeypatch.setattr(app_module, "fetch_all_issues", lambda config: FAKE_ISSUES)

    response = client.get("/insights")

    assert response.status_code == 200
    body = response.json()
    assert body["total_issues"] == 2
    assert body["open_issue_count"] == 1
    assert body["by_status_category"] == {"In Progress": 1, "Done": 1}


def test_insights_returns_502_when_jira_fails(monkeypatch):
    def failing_fetch(config):
        raise JiraError("Jira request failed: 503")

    monkeypatch.setattr(app_module, "get_config", lambda: {})
    monkeypatch.setattr(app_module, "fetch_all_issues", failing_fetch)

    response = client.get("/insights")

    assert response.status_code == 502
    assert response.json() == {"detail": "Jira request failed: 503"}

def test_report_returns_text_and_metrics(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "get_config", lambda: {})
    monkeypatch.setattr(app_module, "fetch_all_issues", lambda config: FAKE_ISSUES)
    monkeypatch.setattr(app_module, "generate_report", lambda metrics: "## Summary\nAll good.")

    response = client.get("/report")

    assert response.status_code == 200
    body = response.json()
    assert body["report"] == "## Summary\nAll good."
    assert body["insights"]["total_issues"] == 2


def test_report_returns_500_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "get_config", lambda: {})
    monkeypatch.setattr(app_module, "fetch_all_issues", lambda config: FAKE_ISSUES)

    response = client.get("/report")

    assert response.status_code == 500
    assert response.json() == {"detail": "Missing ANTHROPIC_API_KEY"}


def test_report_returns_502_when_anthropic_unreachable(monkeypatch):
    def unreachable(metrics):
        raise anthropic.APIConnectionError(
            request=httpx.Request("POST", "https://api.anthropic.com")
        )

    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(app_module, "get_config", lambda: {})
    monkeypatch.setattr(app_module, "fetch_all_issues", lambda config: FAKE_ISSUES)
    monkeypatch.setattr(app_module, "generate_report", unreachable)

    response = client.get("/report")

    assert response.status_code == 502
    assert response.json() == {"detail": "Could not reach the Anthropic API"}
