#!/usr/bin/env python3
import os
import requests
import subprocess
import logging
from pathlib import Path
import openai

# ----------------------------
# Configuration
# ----------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "username/repo"
GIT_DIR = Path(os.getenv("GIT_DIR", "."))

if not all([GITHUB_TOKEN, GITHUB_REPO]):
    raise EnvironmentError("Missing required environment variables.")

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ----------------------------
# GitHub Issues
# ----------------------------
def get_open_github_issues():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    params = {"state": "open"}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return [issue for issue in response.json() if "pull_request" not in issue]
    except Exception as e:
        logging.error(f"Error fetching issues: {e}")
        return []

# ----------------------------
# Create a file for the issue
# ----------------------------
def create_file_for_issue(issue_number):
    file_path = GIT_DIR / f"example_issue{issue_number}.py"
    content = f"# This is auto-generated file for issue #{issue_number}\nprint('Hello from issue {issue_number}')\n"
    file_path.write_text(content)
    subprocess.run(["git", "add", str(file_path)], cwd=GIT_DIR, check=True)
    return file_path

# ----------------------------
# Git operations
# ----------------------------
def run_git(issue_number, branch_name, commit_message):
    try:
        # Switch to main
        subprocess.run(["git", "checkout", "main"], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "pull"], cwd=GIT_DIR, check=True)

        # Create or switch to branch
        existing_branches = subprocess.check_output(["git", "branch"], cwd=GIT_DIR).decode()
        if branch_name in existing_branches:
            subprocess.run(["git", "checkout", branch_name], cwd=GIT_DIR, check=True)
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=GIT_DIR, check=True)

        # Check for changes
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=GIT_DIR).decode().strip()
        if status:
            subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_DIR, check=True)
            subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=GIT_DIR, check=True)
            return True
        else:
            logging.info(f"No changes to commit for branch {branch_name}.")
            return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False

# ----------------------------
# Create Pull Request
# ----------------------------
def create_pr(branch, title, description):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"title": title, "head": branch, "base": "main", "body": description}
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        pr_url = response.json()["html_url"]
        logging.info(f"PR created: {pr_url}")
        return pr_url
    except Exception as e:
        logging.error(f"PR creation failed: {e}")
        return None

# ----------------------------
# Main agent loop
# ----------------------------
def main():
    issues = get_open_github_issues()
    if not issues:
        logging.info("No open GitHub issues.")
        return

    for issue in issues:
        number = issue["number"]
        title = issue["title"]
        description = issue.get("body") or ""
        branch_name = f"issue-{number}-{title[:15].replace(' ', '-')}"
        commit_message = f"Auto commit for issue #{number}"

        logging.info(f"Processing issue #{number}: {title}")

        create_file_for_issue(number)

        if run_git(number, branch_name, commit_message):
            create_pr(branch_name, f"PR for issue #{number}: {title}", description)

if __name__ == "__main__":
    main()
