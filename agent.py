#!/usr/bin/env python3
import os
import requests
import subprocess
import logging
from pathlib import Path
import time

# ----------------------------
# Configuration & Environment
# ----------------------------
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # e.g. "username/repo"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GIT_DIR = Path(os.getenv("GIT_DIR", "."))

if not all([GITHUB_TOKEN, GITHUB_REPO, OPENAI_API_KEY]):
    raise EnvironmentError("Missing one or more required environment variables.")

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

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
        issues = [i for i in response.json() if "pull_request" not in i]
        return issues
    except Exception as e:
        logging.error(f"Error fetching GitHub issues: {e}")
        return []

# ----------------------------
# AI / Plan generator
# ----------------------------
def generate_ai_plan(issue):
    """Generates branch name, commit message, file path and content"""
    issue_id = issue['number']
    issue_title = issue['title'][:30].replace(" ", "-")
    branch_name = f"issue-{issue_id}-{issue_title}"
    commit_message = f"Update for issue #{issue_id}: {issue_title}"
    file_path = GIT_DIR / "src" / f"example_issue{issue_id}.py"
    # If file exists, append a line
    if file_path.exists():
        content = f"# Update at {time.time()}\n"
    else:
        content = f"# Starter file for issue #{issue_id}\nprint('Hello from issue {issue_id}')\n"
    return branch_name, commit_message, file_path, content

# ----------------------------
# Write or update files
# ----------------------------
def write_file(file_path, content):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "a") as f:  # append mode
        f.write(content)
    subprocess.run(["git", "add", str(file_path)], cwd=GIT_DIR, check=True)

# ----------------------------
# Git operations
# ----------------------------
def run_git(branch_name, commit_message):
    try:
        subprocess.run(["git", "checkout", "main"], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "pull"], cwd=GIT_DIR, check=True)

        # Checkout or create branch
        branches = subprocess.check_output(["git", "branch"], cwd=GIT_DIR).decode()
        if branch_name in branches:
            subprocess.run(["git", "checkout", branch_name], cwd=GIT_DIR, check=True)
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=GIT_DIR, check=True)

        # Only commit if there are changes
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=GIT_DIR).decode()
        if status.strip():
            subprocess.run(["git", "commit", "-m", commit_message], cwd=GIT_DIR, check=True)
            subprocess.run(["git", "push", "-u", "origin", branch_name], cwd=GIT_DIR, check=True)
            return True
        else:
            logging.info(f"No changes to commit for branch {branch_name}")
            return False

    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed: {e}")
        return False

# ----------------------------
# Create GitHub PR
# ----------------------------
def create_pr(branch, title):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    data = {"title": title, "head": branch, "base": "main", "body": f"Auto PR for branch {branch}"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["html_url"]
    except Exception as e:
        logging.error(f"PR creation failed: {e}")
        return None

# ----------------------------
# Main agent loop
# ----------------------------
def main():
    issues = get_open_github_issues()
    if not issues:
        logging.info("No open issues found.")
        return

    for issue in issues:
        logging.info(f"Processing issue #{issue['number']}: {issue['title']}")
        branch_name, commit_message, file_path, content = generate_ai_plan(issue)
        write_file(file_path, content)
        changed = run_git(branch_name, commit_message)
        if changed:
            pr_url = create_pr(branch_name, commit_message)
            if pr_url:
                logging.info(f"PR created: {pr_url}")

if __name__ == "__main__":
    main()
