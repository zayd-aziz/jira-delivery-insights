import sys
import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

base_url = os.getenv("JIRA_BASE_URL")
email = os.getenv("JIRA_EMAIL")
token = os.getenv("JIRA_API_TOKEN")
project_key = os.getenv("JIRA_PROJECT_KEY")

url = f"{base_url}/rest/api/3/search/jql"

params = {
    "jql": f"project = {project_key}",
    "maxResults": 50,
    "fields": "summary,status,assignee"
}

required = {
    "JIRA_BASE_URL": base_url,
    "JIRA_EMAIL": email,
    "JIRA_API_TOKEN": token,
    "JIRA_PROJECT_KEY": project_key,
}

missing = [name for name, value in required.items() if not value]
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}")
    sys.exit(1)

me = requests.get(
    f"{base_url}/rest/api/3/myself",
    auth=(email, token),
    headers={"Accept": "application/json"},
    timeout=30,
)

if me.status_code != 200:
    print("Authentication failed — check JIRA_EMAIL and JIRA_API_TOKEN")
    sys.exit(1)

print(f"Authenticated as {me.json()['displayName']}")

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
