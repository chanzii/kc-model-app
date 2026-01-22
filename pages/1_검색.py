import streamlit as st
import pandas as pd
from lib.data_io import load_df
from lib.rules import normalize_fiber_key, expiry_status

st.title("🔍 검색")

rep = load_df("rep")
style = load_df("style")
hubs = load_df("hubs")
cats = load_df("cats")
fibers = load_df("fibers")

# 마스터(활성만)
active_hubs = hubs[hubs.get("active","").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else []
active_cats = cats[cats.get("active","").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else []

active_fibers_df = fibers[fibers.get("active","").str.upper() == "TRUE"] if not fibers.empty else pd.DataFrame(columns=["fiber","sort_order"])
active_fibers = active_fibers_df["fiber"].tolist()

# 섬유 정렬용 맵
fiber_order = {}
if not active_fibers_df.empty:
    for _, r in active_fibers_df.iterrows():
        try:
            fiber_order[r["fiber"]] = int(r.get("sort_order", "9999") or 9999)
        except Exception:
            fiber_order[r["fiber"]] = 9999

tab1, tab2 = st.tabs(["조건 검색", "STYLENO 검색"])

# ----------------------------
# 조건 검색
# ----------------------------
with tab1:
    st.subheader("조건으로 대표모델 찾기 (일부만 선택해도 검색됨)")

    col1, col2, col3 = st.columns(3)
    with col1:
        hub = st.selectbox("생산거점", options=["(전체)"] + active_hubs)
    with col2:
        cat = st.selectbox("품목군", options=["(전체)"] + active_cats)
    with col3:
        selected = st.multiselect("조성섬유(선택 시: 정확히 일치)", options=active_fibers)

    if st.button("검색", type="primary", key="btn_cond_search"):
        if rep.empty:
            st.error("대표모델 데이터가 없습니다.")
            st.stop()

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
            # 상태 컬럼 붙여서 리스트 출력
            statuses = []
            for _, r in df.iterrows():
                icon, msg = expiry_status(r.get("expiry_date",""))
                statuses.append(f"{icon} {msg}")
            df = df.copy()
            df["status"] = statuses

            # 보기 좋은 컬럼만
            st.dataframe(
                df[["rep_id","hub","category","fiber_key","kc_no","cert_date","expiry_date","status","memo"]],
                use_container_width=True
            )

            st.caption("조성섬유를 선택하지 않으면 조성 조건은 적용되지 않습니다. (선택하면 정확히 일치로 필터)")

# ----------------------------
# STYLENO 검색 (prefix/contains)
# ----------------------------
with tab2:
    st.subheader("STYLENO로 KC 찾기 (정확/부분검색)")

    q = st.text_input("검색어", placeholder="예: ABC / ABC12 / 123 등")
    mode = st.radio("검색 방식", options=["앞에서 일치(prefix)", "포함(contains)"], horizontal=True)
    min_len = 2

    if q and len(q.strip()) >= min_len:
        q2 = q.strip()

        if style.empty:
            st.info("동일모델(style_map) 데이터가 비어있습니다.")
        else:
            s_upper = style["style_no"].str.upper()

            if mode.startswith("앞에서"):
                hit_style = style[s_upper.str.startswith(q2.upper())]
            else:
                hit_style = style[s_upper.str.contains(q2.upper(), na=False)]

            if hit_style.empty:
                st.warning("결과가 없습니다.")
            else:
                # rep join
                if rep.empty:
                    out = hit_style.copy()
                    out["kc_no"] = ""
                    out["expiry_date"] = ""
                    out["hub"] = ""
                    out["category"] = ""
                    out["fiber_key"] = ""
                else:
                    out = hit_style.merge(
                        rep[["rep_id","kc_no","expiry_date","hub","category","fiber_key"]],
                        on="rep_id", how="left"
                    )

                # 상태 뱃지
                badges = []
                for _, r in out.iterrows():
                    icon, msg = expiry_status(r.get("expiry_date",""))
                    badges.append(f"{icon} {msg}")
                out["status"] = badges

                # 결과 많으면 제한
                if len(out) > 100:
                    st.warning(f"결과가 {len(out)}개입니다. (상위 100개만 표시) 더 구체적으로 입력해 주세요.")
                    out = out.head(100)

                st.dataframe(out[["style_no","kc_no","status","hub","category","fiber_key","rep_id"]], use_container_width=True)

    elif q:
        st.caption(f"최소 {min_len}글자 이상 입력하면 검색됩니다.")
