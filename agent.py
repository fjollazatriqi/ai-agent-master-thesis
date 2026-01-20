#!/usr/bin/env python3
from dotenv import load_dotenv
load_dotenv()

import os
import requests
import subprocess
import logging
from pathlib import Path
from openai import OpenAI

# ----------------------------
# Configuration & Environment
# ----------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "username/repo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
GIT_DIR = Path(".").resolve()


if not all([GITHUB_TOKEN, GITHUB_REPO, OPENAI_API_KEY]):
    raise EnvironmentError("Missing required environment variables.")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ----------------------------
# Slack Notification
# ----------------------------
def notify_slack(issue_number, issue_title, pr_url):
    if not SLACK_WEBHOOK_URL:
        logging.warning("SLACK_WEBHOOK_URL not set — skipping Slack notification.")
        return

    payload = {
        "text": (
            f"✅ *Tasku #{issue_number} u përfundua*\n"
            f"*Titulli:* {issue_title}\n"
            f"*Link i Pull Request-it:* {pr_url}"
        )
    }

    try:
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Slack notification failed: {e}")

# ----------------------------
# GitHub Issues
# ----------------------------
def get_open_github_issues():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    params = {"state": "open"}

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return [
            issue for issue in response.json()
            if "pull_request" not in issue
        ]
    except Exception as e:
        logging.error(f"Error fetching GitHub issues: {e}")
        return []

# ----------------------------
# AI Planning
# ----------------------------
def generate_ai_plan(task_description, issue_number):
    clean_title = (
        task_description[:30]
        .replace(" ", "-")
        .replace("–", "")
        .replace("—", "")
    )

    branch_name = f"issue-{issue_number}-{clean_title}"
    pr_title = f"Update for issue #{issue_number}: {task_description[:50]}"
    pr_description = f"Auto-generated PR for issue #{issue_number}:\n{task_description}"

    prompt = f"""
Write a Python code snippet for the following task:

{task_description}

Rules:
- Only valid Python code
- No explanations
- No markdown
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a senior Python developer."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    code_snippet = response.choices[0].message.content.strip()
    if not code_snippet:
        raise RuntimeError("Empty AI response")

    return {
        "branch_name": branch_name,
        "pr_title": pr_title,
        "pr_description": pr_description,
        "files": [
            {
                "path": f"src/example_issue{issue_number}.py",
                "content": code_snippet
            }
        ]
    }

# ----------------------------
# File Handling + Git
# ----------------------------
def write_files(files):
    for file in files:
        path = GIT_DIR / file["path"]
        path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if path.exists() else "w"
        with open(path, mode, encoding="utf-8") as f:
            if mode == "a":
                f.write("\n\n")
            f.write(file["content"])

        subprocess.run(["git", "add", str(path)], cwd=GIT_DIR, check=True)

def run_git(branch_name, commit_message):
    try:
        subprocess.run(["git", "checkout", "main"], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "pull"], cwd=GIT_DIR, check=True)

        branches = subprocess.check_output(["git", "branch"], cwd=GIT_DIR).decode()
        if branch_name in branches:
            subprocess.run(["git", "checkout", branch_name], cwd=GIT_DIR, check=True)
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=GIT_DIR, check=True)

        has_changes = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=GIT_DIR
        ).returncode != 0

        if has_changes:
            subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_DIR, check=True)
            subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=GIT_DIR, check=True)

        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False

# ----------------------------
# GitHub Pull Request
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
# Main
# ----------------------------
def main():
    issues = get_open_github_issues()
    if not issues:
        logging.info("No open GitHub issues found.")
        return

    for issue in issues:
        issue_number = issue["number"]
        title = issue["title"]

        logging.info(f"Processing issue #{issue_number}: {title}")

        plan = generate_ai_plan(title, issue_number)
        write_files(plan["files"])

        if run_git(plan["branch_name"], plan["pr_title"]):
            pr_url = create_pr(
                plan["branch_name"],
                plan["pr_title"],
                plan["pr_description"]
            )

            if pr_url:
                logging.info(f"PR created: {pr_url}")
                notify_slack(issue_number, title, pr_url)

if __name__ == "__main__":
    main()
