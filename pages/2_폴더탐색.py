import streamlit as st
import pandas as pd
from lib.data_io import load_df
from lib.rules import expiry_status

st.title("📂 폴더 탐색")

rep = load_df("rep")
hubs = load_df("hubs")
cats = load_df("cats")
fibers = load_df("fibers")

# 호환: rep_style_no 없으면 추가
if not rep.empty and "rep_style_no" not in rep.columns:
    rep["rep_style_no"] = ""

if rep.empty:
    st.info("대표모델 데이터가 없습니다.")
    st.stop()

# 활성 마스터 기반 옵션 (없으면 rep 데이터에서 뽑기)
active_hubs = hubs[hubs.get("active", "").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else []
active_cats = cats[cats.get("active", "").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else []

hub_options = active_hubs if active_hubs else sorted(rep["hub"].astype(str).unique().tolist())
cat_options = active_cats if active_cats else sorted(rep["category"].astype(str).unique().tolist())
fiber_options = sorted(rep["fiber_key"].astype(str).unique().tolist())

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

    display_cols = [
        "스타일",
        "생산처",
        "분류",
        "조성섬유",
        "인증번호",
        "신고일",
        "만료일",
        "잔여기간",
        "등록",
        "등록일",
    ]
    display_cols = [c for c in display_cols if c in df_display.columns]
    return df_display[display_cols]

st.caption("생산처/분류/조성섬유를 일부만 선택해도 아래 결과가 필터되어 표시됩니다.")

col1, col2, col3 = st.columns(3)
with col1:
    hub = st.selectbox("생산처", options=["(전체)"] + hub_options)
with col2:
    cat = st.selectbox("분류", options=["(전체)"] + cat_options)
with col3:
    fiber_key = st.selectbox("조성섬유", options=["(전체)"] + fiber_options)

df = rep.copy()

if hub != "(전체)":
    df = df[df["hub"] == hub]
if cat != "(전체)":
    df = df[df["category"] == cat]
if fiber_key != "(전체)":
    df = df[df["fiber_key"] == fiber_key]

# 경로 텍스트 (선택된 것만)
parts = []
if hub != "(전체)":
    parts.append(hub)
if cat != "(전체)":
    parts.append(cat)
if fiber_key != "(전체)":
    parts.append(fiber_key)

if parts:
    st.markdown("**현재 필터:** `" + " > ".join(parts) + "`")
else:
    st.markdown("**현재 필터:** `(전체)`")

if df.empty:
    st.warning("조건에 맞는 대표모델이 없습니다.")
else:
    st.dataframe(make_korean_table_from_rep(df), use_container_width=True)
