import subprocess
from pathlib import Path
import pandas as pd
import streamlit as st

REPO_LOCAL = Path("repo_cache")
DATA_DIR = REPO_LOCAL / "data"

FILE_MAP = {
    "rep": "rep_models.csv",
    "style": "style_map.csv",
    "hubs": "master_hubs.csv",
    "cats": "master_categories.csv",
    "fibers": "master_fibers.csv",
    "users": "users.csv",
    "audit": "audit_log.csv",
}

def _run_git(args, allow_fail=False):
    """git 실행 + 실패 시 에러 메시지까지 확보"""
    p = subprocess.run(
        ["git", "-C", str(REPO_LOCAL), *args],
        capture_output=True, text=True
    )
    if p.returncode != 0 and not allow_fail:
        raise RuntimeError(f"git {' '.join(args)} 실패\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    return p

def _ensure_repo_ready():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # ✅ Streamlit Cloud에서 commit 하려면 user.name/email이 꼭 필요
    _run_git(["config", "user.email", "streamlit@app.local"], allow_fail=True)
    _run_git(["config", "user.name", "streamlit-bot"], allow_fail=True)

def _set_remote_with_token():
    token = st.secrets["GH_TOKEN"]
    repo = st.secrets["GH_REPO"]
    url = f"https://{token}@github.com/{repo}.git"

    # origin이 있으면 url 교체, 없으면 추가
    remotes = _run_git(["remote"], allow_fail=True).stdout.strip().splitlines()
    if "origin" in remotes:
        _run_git(["remote", "set-url", "origin", url], allow_fail=True)
    else:
        _run_git(["remote", "add", "origin", url], allow_fail=True)

def _path_for(key: str) -> Path:
    if key not in FILE_MAP:
        raise ValueError(f"Unknown data key: {key} (FILE_MAP에 추가 필요)")
    return DATA_DIR / FILE_MAP[key]

def load_df(key: str) -> pd.DataFrame:
    _ensure_repo_ready()
    p = _path_for(key)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, dtype=str).fillna("")
    except Exception:
        return pd.DataFrame()

def save_df_and_commit(key: str, df: pd.DataFrame, commit_msg: str = "update data") -> None:
    """
    repo_cache/data에 저장 -> git add/commit/push
    실패하면 Streamlit 화면에 이유를 표시(디버그).
    """
    try:
        _ensure_repo_ready()
        p = _path_for(key)

        df_out = df.copy()
        for c in df_out.columns:
            df_out[c] = df_out[c].astype(str)

        df_out.to_csv(p, index=False, encoding="utf-8")

        _set_remote_with_token()

        branch = st.secrets.get("GH_BRANCH", "main")

        # 충돌 최소화: pull 먼저
        _run_git(["pull", "origin", branch], allow_fail=True)

        _run_git(["add", f"data/{p.name}"])

        # 변경 없으면 끝
        status = _run_git(["status", "--porcelain"]).stdout.strip()
        if not status:
            st.toast("변경 없음(커밋 생략)", icon="ℹ️")
            return

        _run_git(["commit", "-m", commit_msg])

        # ✅ push는 branch 명시
        _run_git(["push", "origin", branch])

        st.toast("✅ GitHub 커밋/푸시 완료", icon="✅")

    except Exception as e:
        st.error("❌ GitHub 저장(커밋/푸시) 실패")
        st.exception(e)
        # 여기서 멈춰서 실패를 확실히 알게 함
        st.stop()
