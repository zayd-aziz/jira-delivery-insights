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
config = get_config()
base_url = config["JIRA_BASE_URL"]
email = config["JIRA_EMAIL"]
token = config["JIRA_API_TOKEN"]
project_key = config["JIRA_PROJECT_KEY"]

url = f"{base_url}/rest/api/3/search/jql"

params = {
    "jql": f"project = {project_key}",
    "maxResults": 50,
    "fields": "summary,status,assignee"
}
display_name = check_auth(config)
print(f"Authenticated as {display_name}")


#print(f"Authenticated as {me.json()['displayName']}")

all_issues = []

while True:
    try: 
        response = requests.get(
            url,
            auth=(email, token),
            headers={"Accept": "application/json"},
            params=params,
            timeout=30
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
    print(response.status_code)
    print(len(data["issues"]))

    for issue in data["issues"]:
        print(f"{issue['key']}: {issue['fields']['summary']}")

    next_token = data.get("nextPageToken")
    if not next_token:
        break
    params["nextPageToken"] = next_token

os.makedirs("output", exist_ok=True)

with open("output/issues.json", "w") as f:
    json.dump(all_issues, f, indent=2)

print(f"Wrote {len(all_issues)} issues to output/issues.json")
