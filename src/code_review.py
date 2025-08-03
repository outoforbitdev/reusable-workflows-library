import os
import json
import requests

GITHUB_API_URL = "https://api.github.com"

def get_github_env():
    return {
        "token": os.environ["GITHUB_TOKEN"],
        "repo": os.environ["GITHUB_REPOSITORY"],
        "event_path": os.environ["GITHUB_EVENT_PATH"]
    }

def get_pr_info(event_path):
    with open(event_path, 'r') as f:
        event_data = json.load(f)

    pr_number = event_data["pull_request"]["number"]
    pr_title = event_data["pull_request"]["title"]
    pr_body = event_data["pull_request"]["body"]
    return pr_number, pr_title, pr_body

def get_diff(owner, repo, pr_number):
    url = f"https://patch-diff.githubusercontent.com/raw/{owner}/{repo}/pull/{pr_number}.diff"
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def build_prompt(diff, title, body):
    return f"""
You are an expert code reviewer. Please analyze the following pull request and provide feedback.

PR Title: {title}
PR Description: {body}

Diff:
{diff}

Expected Output Format (as JSON):
[
  {{
    "file": "relative/path/to/file.py",
    "line": 42,
    "comment": "blocking: explain why this change is problematic"
  }},
  ...
]

Please only include useful feedback in the specified format.
"""

def get_model_response(prompt):
    # Replace this with your actual model call (OpenAI, Claude, etc.)
    # Here's a placeholder for OpenAI
    import openai
    openai.api_key = os.environ["OPENAI_API_KEY"]
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code review assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response["choices"][0]["message"]["content"]

def post_comments(comments, repo, pr_number, token):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    for item in comments:
        file_path = item["file"]
        line = item["line"]
        comment = item["comment"]

        payload = {
            "body": comment,
            "path": file_path,
            "line": line,
            "side": "RIGHT"
        }

        url = f"{GITHUB_API_URL}/repos/{repo}/pulls/{pr_number}/comments"
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code >= 300:
            print(f"Failed to post comment: {response.status_code} - {response.text}")

def main():
    env = get_github_env()
    owner, repo = env["repo"].split("/")
    pr_number, pr_title, pr_body = get_pr_info(env["event_path"])
    
    diff = get_diff(owner, repo, pr_number)
    prompt = build_prompt(diff, pr_title, pr_body)
    print(prompt)
    # model_output = get_model_response(prompt)

    # try:
    #     comments = json.loads(model_output)
    #     post_comments(comments, env["repo"], pr_number, env["token"])
    # except json.JSONDecodeError:
    #     print("Model response could not be parsed as JSON:")
    #     print(model_output)

if __name__ == "__main__":
    main()
