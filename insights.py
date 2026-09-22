from datetime import datetime, timezone
import json
from collections import Counter


def load_issues(path="output/issues.json"):
    with open(path) as f:
        return json.load(f)

def is_done(issue):
    return issue["fields"]["status"]["statusCategory"]["key"] == "done"

def count_by_status_category(issues):
    return Counter(
        issue["fields"]["status"]["statusCategory"]["name"] for issue in issues
    )

def count_open_by_assignee(issues):
    counts = Counter()
    for issue in issues:
        if is_done(issue):
            continue
        assignee = issue["fields"]["assignee"]
        name = assignee["displayName"] if assignee else "Unassigned"
        counts[name] += 1
    return counts

def parse_jira_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")


def open_issue_ages(issues, now=None):
    now = now or datetime.now(timezone.utc)
    ages = []
    for issue in issues:
        if is_done(issue):
            continue
        created = parse_jira_datetime(issue["fields"]["created"])
        ages.append((issue["key"], (now - created).days))
    return sorted(ages, key=lambda pair: pair[1], reverse=True)

def main():
    issues = load_issues()
    print(f"Loaded {len(issues)} issues\n")

    print("By status category:")
    for category, count in count_by_status_category(issues).items():
        print(f"  {category}: {count}")

    print("\nOpen issues by assignee:")
    for name, count in count_open_by_assignee(issues).most_common():
        print(f"  {name}: {count}")

    ages = open_issue_ages(issues)
    if ages:
        average = sum(days for _, days in ages) / len(ages)
        print(f"\nOpen issue age: average {average:.1f} days")
        print("Oldest open issues:")
        for key, days in ages[:5]:
            print(f"  {key}: {days} days")
            
if __name__ == "__main__":
    main()
    

