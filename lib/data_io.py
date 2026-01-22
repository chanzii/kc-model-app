import os
import subprocess
from pathlib import Path
import pandas as pd
import streamlit as st

# repo_cache 위치 (app.py에서 sync_repo_cache가 최신으로 pull/clone 해둠)
REPO_LOCAL = Path("repo_cache")
DATA_DIR = REPO_LOCAL / "data"

# load_df에서 쓰는 키 -> 실제 파일명 매핑
FILE_MAP = {
    "rep": "rep_models.csv",
    "style": "style_map.csv",
    "hubs": "master_hubs.csv",
    "cats": "master_categories.csv",
    "fibers": "master_fibers.csv",
    "users": "users.csv",
    "audit": "audit_log.csv",
}

def _ensure_repo_ready() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def _git(*args: str) -> None:
    subprocess.run(["git", "-C", str(REPO_LOCAL), *args], check=True)

def _set_remote_with_token() -> None:
    """
    Streamlit에서 push하려면 remote URL에 토큰이 들어가야 함
    """
    token = st.secrets["GH_TOKEN"]
    repo = st.secrets["GH_REPO"]
    url = f"https://{token}@github.com/{repo}.git"
    # origin이 없거나 URL이 다르면 맞춰줌
    try:
        _git("remote", "set-url", "origin", url)
    except Exception:
        _git("remote", "add", "origin", url)

def _path_for(key: str) -> Path:
    if key not in FILE_MAP:
        raise ValueError(f"Unknown data key: {key}. FILE_MAP에 추가 필요")
    return DATA_DIR / FILE_MAP[key]

def load_df(key: str) -> pd.DataFrame:
    """
    repo_cache/data에서 CSV를 읽음. 없으면 빈 DF 반환.
    """
    _ensure_repo_ready()
    p = _path_for(key)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, dtype=str).fillna("")
    except Exception:
        # CSV 깨졌을 때 앱이 완전히 죽지 않도록
        return pd.DataFrame()

def save_df_and_commit(key: str, df: pd.DataFrame, commit_msg: str = "update data") -> None:
    """
    repo_cache/data에 저장 -> git add/commit/push 까지 수행
    """
    _ensure_repo_ready()
    p = _path_for(key)

    # 전부 문자열로 저장(형변환 이슈 방지)
    df_out = df.copy()
    for c in df_out.columns:
        df_out[c] = df_out[c].astype(str)

    df_out.to_csv(p, index=False, encoding="utf-8")

    # git commit/push
    _set_remote_with_token()

    # pull 먼저 한 번(충돌 최소화)
    try:
        _git("pull", "--quiet")
    except Exception:
        pass

    _git("add", f"data/{p.name}")

    # 변경이 없으면 commit 생략
    status = subprocess.run(
        ["git", "-C", str(REPO_LOCAL), "status", "--porcelain"],
        capture_output=True, text=True
    ).stdout.strip()

    if not status:
        return

    try:
        _git("commit", "-m", commit_msg)
    except Exception:
        # 커밋할 게 없거나(동일) 등
        return

    _git("push", "--quiet")
