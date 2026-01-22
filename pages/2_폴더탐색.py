import streamlit as st
import pandas as pd
from lib.data_io import load_df
from lib.rules import expiry_status

st.title("📂 폴더 탐색")

rep = load_df("rep")
hubs = load_df("hubs")
cats = load_df("cats")

if rep.empty:
    st.info("대표모델 데이터가 없습니다.")
    st.stop()

# 활성 마스터 기반 옵션 구성
active_hubs = hubs[hubs.get("active","").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else sorted(rep["hub"].unique().tolist())
active_cats = cats[cats.get("active","").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else sorted(rep["category"].unique().tolist())

hub = st.selectbox("1) 생산거점", options=[""] + active_hubs)

if hub:
    rep1 = rep[rep["hub"] == hub]
    cat_list = [c for c in active_cats if c in rep1["category"].unique().tolist()]
    cat = st.selectbox("2) 품목군", options=[""] + cat_list)

    if cat:
        rep2 = rep1[rep1["category"] == cat]
        fiber_list = sorted(rep2["fiber_key"].unique().tolist())
        fiber_key = st.selectbox("3) 조성(폴더)", options=[""] + fiber_list)

        if fiber_key:
            hit = rep2[rep2["fiber_key"] == fiber_key]
            st.markdown(f"**경로:** `{hub} > {cat} > {fiber_key}`")

            rows = []
            for _, r in hit.iterrows():
                icon, msg = expiry_status(r.get("expiry_date",""))
                rows.append({
                    "rep_id": r.get("rep_id",""),
                    "KC번호": r.get("kc_no",""),
                    "상태": f"{icon} {msg}",
                    "인증일": r.get("cert_date",""),
                    "유효기간": r.get("expiry_date",""),
                    "메모": r.get("memo",""),
                })

            st.dataframe(pd.DataFrame(rows), use_container_width=True)
