import subprocess
from pathlib import Path

REPO_LOCAL = Path("repo_cache")

def sync_repo_or_pull(gh_token: str, gh_repo: str, gh_branch: str = "main") -> bool:
    """
    GitHub 저장소를 repo_cache로 clone/pull 해서 최신 상태로 맞춥니다.
    """
    repo_url = f"https://{gh_token}@github.com/{gh_repo}.git"
    try:
        if REPO_LOCAL.exists():
            subprocess.run(["git", "-C", str(REPO_LOCAL), "pull", "--quiet"], check=True)
        else:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", gh_branch, repo_url, str(REPO_LOCAL)],
                check=True
            )
        (REPO_LOCAL / "data").mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False
