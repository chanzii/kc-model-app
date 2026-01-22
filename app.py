import streamlit as st
from lib.github_sync import sync_repo_or_pull
from lib.session import sidebar_user_controls

st.set_page_config(page_title="KC 대표/동일모델 관리", layout="wide")
st.title("KC 대표/동일모델 관리")

# GitHub repo 동기화
sync_repo_or_pull()

# 사이드바(사용자/관리자 모드)
sidebar_user_controls()

st.info("왼쪽 메뉴에서 검색 / 폴더 탐색 / 대표모델 / 동일모델 / 마스터관리로 이동하세요.")
