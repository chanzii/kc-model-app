import subprocess
from pathlib import Path

REPO_LOCAL = Path("repo_cache")

def sync_repo_cache(gh_token: str, gh_repo: str, gh_branch: str = "main") -> bool:
    """
    GitHub 저장소를 repo_cache로 clone/pull 해서 최신 상태로 맞춥니다.
    Streamlit 리부트/재시작 시 로컬이 날아가도, 여기서 다시 복원됩니다.
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
        # data 폴더 없으면 만들어두기
        (REPO_LOCAL / "data").mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False
