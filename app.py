import streamlit as st
from lib.session import sidebar_user_controls
from lib.github_sync import sync_repo_cache

st.set_page_config(page_title="KC 대표/동일모델 관리", layout="wide")
st.title("KC 대표/동일모델 관리")

# ✅ 앱 부팅 시 1회: GitHub -> repo_cache 최신화
if "repo_synced" not in st.session_state:
    ok = sync_repo_cache(
        gh_token=st.secrets["GH_TOKEN"],
        gh_repo=st.secrets["GH_REPO"],
        gh_branch=st.secrets.get("GH_BRANCH", "main"),
    )
    st.session_state["repo_synced"] = True
    if not ok:
        st.warning("⚠️ GitHub 동기화에 실패했습니다. (네트워크/토큰/레포 설정 확인)")

# 사이드바(사용자/관리자 모드)
sidebar_user_controls()

st.info("왼쪽 메뉴에서 검색 / 폴더 탐색 / 대표모델 / 동일모델 / 마스터관리로 이동하세요.")
