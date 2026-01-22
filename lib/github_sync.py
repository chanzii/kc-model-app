import streamlit as st
import subprocess
from pathlib import Path

REPO_LOCAL = Path("repo_cache")

def sync_repo_or_pull():
    gh_token  = st.secrets["GH_TOKEN"]
    gh_repo   = st.secrets["GH_REPO"]
    gh_branch = st.secrets.get("GH_BRANCH", "main")

    repo_url = f"https://{gh_token}@github.com/{gh_repo}.git"

    try:
        if REPO_LOCAL.exists():
            subprocess.run(["git", "-C", str(REPO_LOCAL), "pull", "--quiet"], check=True)
        else:
            subprocess.run([
                "git", "clone", "--depth", "1",
                "--branch", gh_branch,
                repo_url, str(REPO_LOCAL)
            ], check=True)
    except subprocess.CalledProcessError as e:
        st.warning(f"GitHub 동기화 실패: {e}")
        return

    (REPO_LOCAL / "data").mkdir(parents=True, exist_ok=True)
