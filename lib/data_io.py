from pathlib import Path
import pandas as pd
import streamlit as st
from lib.github_api import commit_file_to_github

REPO_LOCAL = Path("repo_cache")
DATA_DIR = REPO_LOCAL / "data"

FILES = {
    "rep": "rep_models.csv",
    "style": "style_map.csv",
    "hubs": "master_hubs.csv",
    "cats": "master_categories.csv",
    "fibers": "master_fibers.csv",
    "audit": "audit_log.csv",
}

def _path(key: str) -> Path:
    return DATA_DIR / FILES[key]

def load_df(key: str) -> pd.DataFrame:
    """
    repo_cache/data/*.csv 를 DataFrame으로 로드
    (없으면 빈 DF)
    """
    p = _path(key)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p, dtype=str).fillna("")
    except Exception:
        # 깨졌을 때 앱이 죽지 않게 빈 DF 반환
        return pd.DataFrame()

def save_df_and_commit(key: str, df: pd.DataFrame, commit_msg: str) -> bool:
    """
    DF -> repo_cache/data/*.csv 저장 -> GitHub에 커밋
    """
    p = _path(key)
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(p, index=False, encoding="utf-8-sig")

    ok, err = commit_file_to_github(str(p), f"data/{FILES[key]}", message=commit_msg)
    if not ok:
        st.error(f"❌ GitHub 커밋 실패: {err}")
        return False
    return True
