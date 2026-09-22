from types import SimpleNamespace
from unittest.mock import patch

from report import MODEL, build_insights, describe_issue, generate_report


def make_issue(key, summary, category, assignee=None, status_name=None):
    category_names = {"new": "To Do", "indeterminate": "In Progress", "done": "Done"}
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "status": {
                "name": status_name or category_names[category],
                "statusCategory": {"key": category, "name": category_names[category]},
            },
            "assignee": {"displayName": assignee} if assignee else None,
            "created": "2026-09-01T10:00:00.000+0000",
        },
    }


def test_describe_issue_unassigned():
    issue = make_issue("PWW-1", "UCF early action", "new")
    assert describe_issue(issue, 15) == {
        "key": "PWW-1",
        "summary": "UCF early action",
        "status": "To Do",
        "assignee": "Unassigned",
        "age_days": 15,
    }


def test_describe_issue_uses_status_name_and_assignee():
    issue = make_issue(
        "PWW-9", "UM Early Decision", "new",
        assignee="Zayd Aziz", status_name="College Applications",
    )
    result = describe_issue(issue, 3)
    assert result["status"] == "College Applications"
    assert result["assignee"] == "Zayd Aziz"


def test_build_insights_counts():
    issues = [
        make_issue("PWW-1", "A", "new"),
        make_issue("PWW-2", "B", "indeterminate", assignee="Zayd Aziz"),
        make_issue("PWW-3", "C", "done", assignee="Zayd Aziz"),
    ]
    insights = build_insights(issues)
    assert insights["total_issues"] == 3
    assert insights["open_issue_count"] == 2
    assert insights["by_status_category"] == {"To Do": 1, "In Progress": 1, "Done": 1}
    assert insights["open_by_assignee"] == {"Unassigned": 1, "Zayd Aziz": 1}
    assert {i["key"] for i in insights["oldest_open_issues"]} == {"PWW-1", "PWW-2"}


def test_generate_report_returns_only_text_blocks():
    fake_message = SimpleNamespace(content=[
        SimpleNamespace(type="thinking", thinking="Let me look at the data..."),
        SimpleNamespace(type="text", text="## Summary\nAll good."),
    ])
    with patch("report.anthropic.Anthropic") as mock_client_class:
        mock_client_class.return_value.messages.create.return_value = fake_message
        result = generate_report({"total_issues": 0})

    assert result == "## Summary\nAll good."
    call_kwargs = mock_client_class.return_value.messages.create.call_args.kwargs
    assert call_kwargs["model"] == MODEL
