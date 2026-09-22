import sys
import os
import requests
from dotenv import load_dotenv
import json

REQUIRED_VARS = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]


def get_config():
    load_dotenv()
    config = {name: os.getenv(name) for name in REQUIRED_VARS}
    missing = [name for name, value in config.items() if not value]
    if missing:
        print(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)
    return config
    
def check_auth(config):
    me = requests.get(
        f"{config['JIRA_BASE_URL']}/rest/api/3/myself",
        auth=(config["JIRA_EMAIL"], config["JIRA_API_TOKEN"]),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if me.status_code != 200:
        print("Authentication failed — check JIRA_EMAIL and JIRA_API_TOKEN")
        sys.exit(1)
    return me.json()["displayName"]

def fetch_all_issues(config):
    url = f"{config['JIRA_BASE_URL']}/rest/api/3/search/jql"
    params = {
        "jql": f"project = {config['JIRA_PROJECT_KEY']}",
        "maxResults": 50,
        "fields": "summary,status,assignee",
    }
    auth = (config["JIRA_EMAIL"], config["JIRA_API_TOKEN"])
    all_issues = []

    while True:
        try:
            response = requests.get(
                url,
                auth=auth,
                headers={"Accept": "application/json"},
                params=params,
                timeout=30,
            )
            response.raise_for_status()
        except requests.exceptions.HTTPError as error:
            print(f"Request failed: {error}")
            print(response.text)
            sys.exit(1)
        except requests.exceptions.RequestException as error:
            print(f"Connection or request failed: {error}")
            sys.exit(1)

        data = response.json()
        all_issues.extend(data["issues"])

        next_token = data.get("nextPageToken")
        if not next_token:
            break
        params["nextPageToken"] = next_token

    return all_issues

def save_issues(issues, path="output/issues.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(issues, f, indent=2)
    return path

def main():
    config = get_config()
    display_name = check_auth(config)
    print(f"Authenticated as {display_name}")

    issues = fetch_all_issues(config)
    for issue in issues:
        print(f"{issue['key']}: {issue['fields']['summary']}")

    path = save_issues(issues)
    print(f"Wrote {len(issues)} issues to {path}")

if __name__ == "__main__":
    main()

