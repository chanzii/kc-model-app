import streamlit as st
import pandas as pd
from lib.session import sidebar_user_controls
from lib.github_sync import sync_repo_cache
from lib.data_io import load_df
from lib.rules import normalize_fiber_key, expiry_status

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
        st.warning("⚠️ GitHub 동기화 실패 (토큰/권한/레포 확인)")

# 사이드바(사용자/관리자 모드)
sidebar_user_controls()

st.markdown("## ✅ 조건 검색 (앱 시작 화면)")

rep = load_df("rep")
hubs = load_df("hubs")
cats = load_df("cats")
fibers = load_df("fibers")

if not rep.empty and "rep_style_no" not in rep.columns:
    rep["rep_style_no"] = ""

# 마스터(활성만)
active_hubs = hubs[hubs.get("active", "").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else []
active_cats = cats[cats.get("active", "").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else []
active_fibers_df = fibers[fibers.get("active", "").str.upper() == "TRUE"] if not fibers.empty else pd.DataFrame(columns=["fiber", "sort_order"])
active_fibers = active_fibers_df["fiber"].tolist()

# 섬유 정렬 맵
fiber_order = {}
if not active_fibers_df.empty:
    for _, r in active_fibers_df.iterrows():
        try:
            fiber_order[r["fiber"]] = int(r.get("sort_order", "9999") or 9999)
        except Exception:
            fiber_order[r["fiber"]] = 9999

def make_korean_table_from_rep(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    status_list = []
    for _, r in df.iterrows():
        icon, msg = expiry_status(r.get("expiry_date", ""))
        status_list.append(f"{icon} {msg}")
    df["잔여기간"] = status_list

    df_display = df.rename(columns={
        "rep_style_no": "스타일",
        "hub": "생산처",
        "category": "분류",
        "fiber_key": "조성섬유",
        "kc_no": "인증번호",
        "cert_date": "신고일",
        "expiry_date": "만료일",
        "memo": "등록",
        "updated_at": "등록일",
    })
    cols = ["스타일","생산처","분류","조성섬유","인증번호","신고일","만료일","잔여기간","등록","등록일"]
    cols = [c for c in cols if c in df_display.columns]
    return df_display[cols]

if rep.empty:
    st.info("대표모델 데이터가 없습니다. (대표모델 페이지에서 등록하세요)")
else:
    # 옵션(없으면 rep에서 추출)
    hub_opts = active_hubs if active_hubs else sorted(rep["hub"].astype(str).unique().tolist())
    cat_opts = active_cats if active_cats else sorted(rep["category"].astype(str).unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        hub = st.selectbox("생산처", options=["(전체)"] + hub_opts)
    with col2:
        cat = st.selectbox("분류", options=["(전체)"] + cat_opts)
    with col3:
        selected = st.multiselect("조성섬유(선택 시: 정확히 일치)", options=active_fibers)

    if st.button("검색", type="primary"):
        df = rep.copy()
        if hub != "(전체)":
            df = df[df["hub"] == hub]
        if cat != "(전체)":
            df = df[df["category"] == cat]
        if selected:
            key = normalize_fiber_key(selected, fiber_order)
            df = df[df["fiber_key"] == key]

        if df.empty:
            st.warning("조건에 맞는 대표모델이 없습니다.")
        else:
            st.dataframe(make_korean_table_from_rep(df), use_container_width=True)

    st.caption("조성섬유를 선택하지 않으면 조성 조건은 적용되지 않습니다. (선택하면 정확히 일치로 필터)")

st.markdown("---")
st.info("왼쪽 메뉴에서 폴더 탐색 / 대표모델 / 동일모델 / 마스터관리로 이동하세요.")
