#!/usr/bin/env python3
import os
import requests
import subprocess
import logging
from pathlib import Path
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
    params = {"state": "open"}

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
# AI Planning
# ----------------------------
def generate_ai_plan(task_description, issue_number):
    clean_title = task_description[:30].replace(' ', '-').replace('–','').replace('—','')
    branch_name = f"issue-{issue_number}-{clean_title}"
    pr_title = f"Update for issue #{issue_number}: {task_description[:50]}"
    pr_description = f"Auto-generated PR for issue #{issue_number}:\n{task_description}"

    prompt = f"""
    Write a Python code snippet for the following task:
    {task_description}
    Only return valid Python code, no explanations or comments.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=200
        )
        code_snippet = response.choices[0].message.content.strip()
        if not code_snippet:
            raise ValueError("Empty code snippet returned")
    except Exception as e:
        logging.error(f"OpenAI API call failed: {e}")
        code_snippet = f"# TODO: Implement issue #{issue_number}: {task_description}"

    file_path = f"src/example_issue{issue_number}.py"
    return {
        "branch_name": branch_name,
        "pr_title": pr_title,
        "pr_description": pr_description,
        "files": [
            {"path": file_path, "content": code_snippet}
        ]
    }

# ----------------------------
# File Handling + Git
# ----------------------------
def write_files(files):
    for file in files:
        path = GIT_DIR / file["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            # Append new code instead of overwriting
            with open(path, "a") as f:
                f.write("\n\n" + file["content"])
        else:
            with open(path, "w") as f:
                f.write(file["content"])
        subprocess.run(["git", "add", str(path)], cwd=GIT_DIR, check=True)

def run_git(branch_name, commit_message):
    try:
        subprocess.run(["git", "checkout", "main"], cwd=GIT_DIR, check=True)
        subprocess.run(["git", "pull"], cwd=GIT_DIR, check=True)

        # Checkout or create branch
        existing_branches = subprocess.check_output(["git", "branch"], cwd=GIT_DIR).decode()
        if branch_name in existing_branches:
            subprocess.run(["git", "checkout", branch_name], cwd=GIT_DIR, check=True)
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=GIT_DIR, check=True)

        # Only commit if changes exist
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=GIT_DIR)
        if result.returncode != 0:
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
# Main Loop
# ----------------------------
def main():
    issues = get_open_github_issues()
    if not issues:
        logging.info("No open GitHub issues found.")
        return

    for issue in issues:
        issue_number = issue['number']
        title = issue['title']
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
            else:
                logging.error(f"PR creation failed for branch {plan['branch_name']}")

if __name__ == "__main__":
    main()
