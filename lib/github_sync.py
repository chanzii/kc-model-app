import shutil
import subprocess
from pathlib import Path

REPO_LOCAL = Path("repo_cache")

def sync_repo_cache(gh_token: str, gh_repo: str, gh_branch: str = "main") -> bool:
    repo_url = f"https://{gh_token}@github.com/{gh_repo}.git"
    try:
        if (REPO_LOCAL / ".git").exists():
            subprocess.run(["git", "-C", str(REPO_LOCAL), "pull", "origin", gh_branch, "--quiet"], check=True)
        else:
            # 폴더는 있는데 정상적인 git 저장소가 아니면(이전 실행이 중간에 끊긴 경우 등)
            # 지우고 새로 받는다. 그대로 clone하면 남은 파일과 충돌해서 실패한다.
            if REPO_LOCAL.exists():
                shutil.rmtree(REPO_LOCAL)
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", gh_branch, repo_url, str(REPO_LOCAL)],
                check=True
            )
        (REPO_LOCAL / "data").mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False
