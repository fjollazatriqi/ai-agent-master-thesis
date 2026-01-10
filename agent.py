#!/usr/bin/env python3
import os
import requests
import subprocess
import logging
from pathlib import Path
import json
import openai

# ----------------------------
# Configuration & Environment
# ----------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "username/repo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GIT_DIR = Path(os.getenv("GIT_DIR", "."))

if not all([GITHUB_TOKEN, GITHUB_REPO, OPENAI_API_KEY]):
    raise EnvironmentError("Missing one or more required environment variables.")

openai.api_key = OPENAI_API_KEY

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ----------------------------
# GitHub Issues (Perception)
# ----------------------------
def get_open_github_issues():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    params = {
        "state": "open"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        issues = [
            issue for issue in response.json()
            if "pull_request" not in issue  # exclude PRs
        ]
        return issues
    except Exception as e:
        logging.error(f"Error fetching GitHub issues: {e}")
        return []

# ----------------------------
# AI Reasoning
# ----------------------------
def generate_ai_plan(task_description):
    return {
        "branch_name": f"demo-branch-{task_description[:10].replace(' ', '-')}",
        "pr_title": f"Demo PR for: {task_description[:30]}",
        "pr_description": f"Auto-generated PR description for task:\n{task_description}",
        "files": [
            {"path": "src/example.py", "content": "# starter code\nprint('Hello from AI agent!')"}
        ]
    }

# ----------------------------
# Action: File + Git
# ----------------------------
def write_files(files):
    for file in files:
        path = GIT_DIR / file["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(file["content"])
        subprocess.run(["git", "add", str(path)], cwd=GIT_DIR, check=True)

def run_git(branch_name, commit_message):
    try:
        subprocess.run(["git", "checkout", "main"], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "pull"], cwd=GIT_DIR, check=True)

        # Nëse branch ekziston, thjesht checkout
        existing_branches = subprocess.check_output(["git", "branch"], cwd=GIT_DIR).decode()
        if branch_name in existing_branches:
            subprocess.run(["git", "checkout", branch_name], cwd=GIT_DIR, check=True)
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=GIT_DIR, check=True)

        subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=GIT_DIR, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False


# ----------------------------
# GitHub PR
# ----------------------------
def create_pr(branch, title, description):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {
        "title": title,
        "head": branch,
        "base": "main",
        "body": description
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["html_url"]
    except Exception as e:
        logging.error(f"PR creation failed: {e}")
        return None

# ----------------------------
# Slack Notification
# ----------------------------
def notify_slack(message):
    try:
        requests.post(SLACK_WEBHOOK, json={"text": message})
    except Exception as e:
        logging.error(f"Slack notification failed: {e}")

# ----------------------------
# Main Agent Loop
# ----------------------------
def main():
    issues = get_open_github_issues()
    if not issues:
        logging.info("No open GitHub issues found.")
        return

    for issue in issues:
        logging.info(f"Processing issue #{issue['number']}: {issue['title']}")

        description = issue["body"] or issue["title"]
        plan = generate_ai_plan(description)
        if not plan:
            continue

        if not plan.get("branch_name") or not plan.get("pr_title"):
            logging.warning("Invalid AI output, skipping issue.")
            continue

        write_files(plan.get("files", []))

        if not run_git(plan["branch_name"], plan["pr_title"]):
            continue

        pr_url = create_pr(
            plan["branch_name"],
            plan["pr_title"],
            plan.get("pr_description", "")
        )

        if pr_url:
            notify_slack(f"New PR created for issue #{issue['number']}: {pr_url}")
            logging.info(f"PR created: {pr_url}")

if __name__ == "__main__":
    main()
