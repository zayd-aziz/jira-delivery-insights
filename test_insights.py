from datetime import datetime, timezone

from insights import (
    count_by_status_category,
    count_open_by_assignee,
    open_issue_ages,
    parse_jira_datetime,
)


def make_issue(key, category_key="new", category_name="To Do",
               assignee=None, created="2026-09-01T12:00:00.000+0000"):
    return {
        "key": key,
        "fields": {
            "assignee": {"displayName": assignee} if assignee else None,
            "created": created,
            "status": {"statusCategory": {"key": category_key, "name": category_name}},
        },
    }


def test_count_by_status_category():
    issues = [
        make_issue("A-1"),
        make_issue("A-2"),
        make_issue("A-3", "done", "Done"),
    ]
    assert count_by_status_category(issues) == {"To Do": 2, "Done": 1}


def test_open_by_assignee_skips_done_and_handles_unassigned():
    issues = [
        make_issue("A-1", assignee="Priya"),
        make_issue("A-2", assignee="Priya"),
        make_issue("A-3"),
        make_issue("A-4", "done", "Done", assignee="Priya"),
    ]
    assert count_open_by_assignee(issues) == {"Priya": 2, "Unassigned": 1}


def test_parse_jira_datetime_keeps_offset():
    parsed = parse_jira_datetime("2026-09-08T15:01:44.148-0400")
    assert parsed == datetime(2026, 9, 8, 19, 1, 44, 148000, tzinfo=timezone.utc)


def test_open_issue_ages_counts_whole_days_and_sorts_oldest_first():
    now = datetime(2026, 9, 11, 11, 0, tzinfo=timezone.utc)
    issues = [
        make_issue("A-1", created="2026-09-10T12:00:00.000+0000"),  # 23 hours old
        make_issue("A-2", created="2026-09-01T12:00:00.000+0000"),  # 9 days 23 hours
        make_issue("A-3", "done", "Done", created="2026-08-01T12:00:00.000+0000"),
    ]
    assert open_issue_ages(issues, now=now) == [("A-2", 9), ("A-1", 0)]