import json
import os
import re
import sys

def get_github_env():
    return {
        "token": os.environ["GITHUB_TOKEN"],
        "repo": os.environ["GITHUB_REPOSITORY"],
        "event_path": os.environ["GITHUB_EVENT_PATH"],
        "commit_id": os.environ["GITHUB_COMMIT_SHA"]
    }

def main():
    print("Checking tasks...")
    # Check whether body of PR contains task list items
    env = get_github_env()
    event_path = env["event_path"]
    
    with open(event_path, 'r') as f:
        event_data = json.load(f)
    
    pr_body = event_data["pull_request"]["body"]


    # Regex for GitHub task list items: "- [ ]"
    open_task_pattern = r"- \[ \]"

    open_tasks = re.findall(open_task_pattern, pr_body)

    if open_tasks:
        print(f"❌ Found {len(open_tasks)} open task(s) in the PR description.")
        sys.exit(1)
    else:
        print("✅ No open tasks found in the PR description.")
        sys.exit(0)


if __name__ == "__main__":
    main()
