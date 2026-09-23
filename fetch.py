import sys
import os
import requests
from dotenv import load_dotenv
import json

REQUIRED_VARS = ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY"]

class JiraError(Exception):
    """Raised when Jira config is missing or a Jira request fails."""

def get_config():
    load_dotenv()
    config = {name: os.getenv(name) for name in REQUIRED_VARS}
    missing = [name for name, value in config.items() if not value]
    if missing:
        raise JiraError(f"Missing required environment variables: {', '.join(missing)}")
    return config
    
def check_auth(config):
    me = requests.get(
        f"{config['JIRA_BASE_URL']}/rest/api/3/myself",
        auth=(config["JIRA_EMAIL"], config["JIRA_API_TOKEN"]),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if me.status_code != 200:
        raise JiraError("Authentication failed — check JIRA_EMAIL and JIRA_API_TOKEN")
    return me.json()["displayName"]

def fetch_all_issues(config):
    url = f"{config['JIRA_BASE_URL']}/rest/api/3/search/jql"
    params = {
        "jql": f"project = {config['JIRA_PROJECT_KEY']}",
        "maxResults": 50,
        "fields": "summary,status,assignee,created",
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
            raise JiraError(f"Jira request failed: {error}") from error
        except requests.exceptions.RequestException as error:
            raise JiraError(f"Could not reach Jira: {error}") from error

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
    try:
        config = get_config()
        display_name = check_auth(config)
        print(f"Authenticated as {display_name}")
        issues = fetch_all_issues(config)
    except JiraError as error:
        print(error)
        sys.exit(1)

    for issue in issues:
        print(f"{issue['key']}: {issue['fields']['summary']}")

    path = save_issues(issues)
    print(f"Wrote {len(issues)} issues to {path}")

if __name__ == "__main__":
    main()
