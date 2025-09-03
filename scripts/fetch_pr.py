from github import Github
from config import Settings

def fetch_pr_diff(repo_name: str, pr_number: int):
    token = Settings.GITHUB_TOKEN
    g = Github(token)
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files = pr.get_files()
    changes = {}
    for f in files:
        changes[f.filename] = f.patch
    return changes, pr
