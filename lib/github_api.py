import base64
import json
import requests
import streamlit as st
from urllib.parse import quote as url_quote

def _github_headers():
    token = st.secrets["GH_TOKEN"]
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

def commit_file_to_github(local_path: str, repo_rel_path: str, message: str = ""):
    """
    local_path 파일을 GitHub의 repo_rel_path 경로로 생성/덮어쓰기 커밋합니다.
    예: local_path='repo_cache/data/rep_models.csv'
        repo_rel_path='data/rep_models.csv'
    """
    gh_repo = st.secrets["GH_REPO"]
    gh_branch = st.secrets.get("GH_BRANCH", "main")
    gh_api = f"https://api.github.com/repos/{gh_repo}/contents"
    headers = _github_headers()

    # 파일 내용 base64 인코딩
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    # 기존 파일 sha 확인 (있으면 업데이트, 없으면 생성)
    sha = None
    r = requests.get(
        f"{gh_api}/{url_quote(repo_rel_path)}",
        params={"ref": gh_branch},
        headers=headers
    )
    if r.status_code == 200:
        sha = r.json().get("sha")

    payload = {
        "message": message or f"update {repo_rel_path}",
        "content": content_b64,
        "branch": gh_branch
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(
        f"{gh_api}/{url_quote(repo_rel_path)}",
        headers=headers,
        data=json.dumps(payload)
    )

    if r.status_code in (200, 201):
        return True, None
    try:
        msg = r.json().get("message")
    except Exception:
        msg = r.text
    return False, f"{r.status_code} {msg}"
