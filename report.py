import json
import os
import sys

import anthropic
from dotenv import load_dotenv

from insights import (
    load_issues,
    count_by_status_category,
    count_open_by_assignee,
    open_issue_ages,
)

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """You are an experienced delivery lead reviewing the health of a Jira project.
You will receive pre-computed project metrics as JSON. Write a short delivery report in Markdown with exactly these sections:

## Summary
Two or three sentences on overall health.

## Risks
The most important risks. Tie each one to a specific number or issue key from the data.

## Recommended actions
Three concrete next steps.

Rules:
- Use only the data provided. Do not invent issues, people, dates, or deadlines.
- If the data is too thin to support a conclusion, say so rather than guessing.
- Keep the whole report under 300 words.
- age_days is the number of days since an issue was created, not since it was last updated. Do not describe an issue as stuck, stalled, or slow based on its age alone.
- Only mention an issue key together with facts the data states about that specific issue.
- If two issue summaries suggest the issues may be duplicates, flag them as a risk."""

def describe_issue(issue, age_days):
    fields = issue["fields"]
    assignee = fields["assignee"]
    return {
        "key": issue["key"],
        "summary": fields["summary"],
        "status": fields["status"]["name"],
        "assignee": assignee["displayName"] if assignee else "Unassigned",
        "age_days": age_days,
    }

def build_insights(issues):
    issues_by_key = {issue["key"]: issue for issue in issues}
    ages = open_issue_ages(issues)
    if ages:
        average_age = round(sum(days for _, days in ages) / len(ages), 1)
    else:
        average_age = 0

    return {
        "total_issues": len(issues),
        "by_status_category": dict(count_by_status_category(issues)),
        "open_by_assignee": dict(count_open_by_assignee(issues).most_common()),
        "open_issue_count": len(ages),
        "average_open_age_days": average_age,
                "oldest_open_issues": [
            describe_issue(issues_by_key[key], days) for key, days in ages[:5]
        ],
    }

def generate_report(insights):
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"Project metrics:\n\n{json.dumps(insights, indent=2)}",
            }
        ],
    )
    return "".join(
        block.text for block in message.content if block.type == "text"
    )

def main():
    load_dotenv()
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Missing ANTHROPIC_API_KEY in .env")
        sys.exit(1)

    issues = load_issues()
    insights = build_insights(issues)

    try:
        report = generate_report(insights)
    except anthropic.AuthenticationError:
        print("Anthropic authentication failed — check ANTHROPIC_API_KEY in .env")
        sys.exit(1)
    except anthropic.RateLimitError:
        print("Rate limited by the Anthropic API — wait a minute and try again")
        sys.exit(1)
    except anthropic.APIConnectionError:
        print("Could not reach the Anthropic API — check your internet connection")
        sys.exit(1)
    except anthropic.APIStatusError as error:
        print(f"Anthropic API error {error.status_code}: {error.message}")
        sys.exit(1)

    if not report.strip():
        print("Claude returned no report text — try increasing max_tokens")
        sys.exit(1)

    report_path = "output/report.md"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"Wrote report to {report_path}") 


if __name__ == "__main__":
    main()
