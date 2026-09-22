import json
from collections import Counter


def load_issues(path="output/issues.json"):
    with open(path) as f:
        return json.load(f)


def count_by_status_category(issues):
    return Counter(
        issue["fields"]["status"]["statusCategory"]["name"] for issue in issues
    )


def main():
    issues = load_issues()
    print(f"Loaded {len(issues)} issues\n")

    print("By status category:")
    for category, count in count_by_status_category(issues).items():
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()