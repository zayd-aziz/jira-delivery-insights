import json
from collections import Counter


def load_issues(path="output/issues.json"):
    with open(path) as f:
        return json.load(f)


def count_by_status_category(issues):
    return Counter(
        issue["fields"]["status"]["statusCategory"]["name"] for issue in issues
    )

def count_open_by_assignee(issues):
    counts = Counter()
    for issue in issues:
        if issue["fields"]["status"]["statusCategory"]["key"] == "done":
            continue
        assignee = issue["fields"]["assignee"]
        name = assignee["displayName"] if assignee else "Unassigned"
        counts[name] += 1
    return counts

def main():
    issues = load_issues()
    print(f"Loaded {len(issues)} issues\n")

    print("By status category:")
    for category, count in count_by_status_category(issues).items():
        print(f"  {category}: {count}")

    print("\nOpen issues by assignee:")
    for name, count in count_open_by_assignee(issues).most_common():
        print(f"  {name}: {count}")

if __name__ == "__main__":
    main()
    

