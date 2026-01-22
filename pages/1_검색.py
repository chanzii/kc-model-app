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

# 호환: rep_style_no 없으면 추가
if not rep.empty and "rep_style_no" not in rep.columns:
    rep["rep_style_no"] = ""

# 마스터(활성만)
active_hubs = hubs[hubs.get("active", "").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else []
active_cats = cats[cats.get("active", "").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else []

active_fibers_df = fibers[fibers.get("active", "").str.upper() == "TRUE"] if not fibers.empty else pd.DataFrame(columns=["fiber", "sort_order"])
active_fibers = active_fibers_df["fiber"].tolist()

# 섬유 정렬용 맵
fiber_order = {}
if not active_fibers_df.empty:
    for _, r in active_fibers_df.iterrows():
        try:
            fiber_order[r["fiber"]] = int(r.get("sort_order", "9999") or 9999)
        except Exception:
            fiber_order[r["fiber"]] = 9999

def make_korean_table_from_rep(df: pd.DataFrame) -> pd.DataFrame:
    """rep(df) -> 한글 컬럼/순서로 변환"""
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # 잔여기간 컬럼 생성
    status_list = []
    for _, r in df.iterrows():
        icon, msg = expiry_status(r.get("expiry_date", ""))
        status_list.append(f"{icon} {msg}")
    df["잔여기간"] = status_list

    # 화면용 컬럼명 변경
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

tab1, tab2 = st.tabs(["조건 검색", "STYLENO 검색"])

# ----------------------------
# 조건 검색 (일부만 선택해도 가능)
# ----------------------------
with tab1:
    st.subheader("조건으로 대표모델 찾기 (일부만 선택해도 검색됨)")

    if rep.empty:
        st.info("대표모델 데이터가 없습니다.")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            hub = st.selectbox("생산처", options=["(전체)"] + (active_hubs if active_hubs else sorted(rep["hub"].unique().tolist())))
        with col2:
            cat = st.selectbox("분류", options=["(전체)"] + (active_cats if active_cats else sorted(rep["category"].unique().tolist())))
        with col3:
            selected = st.multiselect("조성섬유(선택 시: 정확히 일치)", options=active_fibers)

        if st.button("검색", type="primary", key="btn_cond_search"):
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

# ----------------------------
# STYLENO 검색 (prefix/contains)
# ----------------------------
with tab2:
    st.subheader("STYLENO로 KC 찾기 (정확/부분검색)")

    q = st.text_input("검색어", placeholder="예: ABC / ABC12 / 123 등")
    mode = st.radio("검색 방식", options=["앞에서 일치(prefix)", "포함(contains)"], horizontal=True)
    min_len = 2

    if not q:
        st.caption(f"최소 {min_len}글자 이상 입력하면 검색됩니다.")
    elif len(q.strip()) < min_len:
        st.caption(f"최소 {min_len}글자 이상 입력하면 검색됩니다.")
    else:
        q2 = q.strip().upper()

        if style.empty:
            st.info("동일모델(style_map) 데이터가 비어있습니다.")
        else:
            s_upper = style["style_no"].astype(str).str.upper()

            if mode.startswith("앞에서"):
                hit_style = style[s_upper.str.startswith(q2)]
            else:
                hit_style = style[s_upper.str.contains(q2, na=False)]

            if hit_style.empty:
                st.warning("결과가 없습니다.")
            else:
                # rep join
                if rep.empty:
                    out = hit_style.copy()
                    out["rep_style_no"] = ""
                    out["hub"] = ""
                    out["category"] = ""
                    out["fiber_key"] = ""
                    out["kc_no"] = ""
                    out["cert_date"] = ""
                    out["expiry_date"] = ""
                    out["memo"] = ""
                    out["updated_at"] = ""
                else:
                    out = hit_style.merge(
                        rep[["rep_id", "rep_style_no", "hub", "category", "fiber_key", "kc_no", "cert_date", "expiry_date", "memo", "updated_at"]],
                        on="rep_id",
                        how="left"
                    )

                # 화면용: style_no(입력한 스타일)도 같이 보여주자
                out = out.rename(columns={"style_no": "검색스타일"})
                out_rep_like = out.rename(columns={"검색스타일": "rep_style_no"})  # 임시로 rep 테이블 변환 함수 재사용
                out_kor = make_korean_table_from_rep(out_rep_like)

                # 첫 컬럼명을 다시 '검색스타일'로 교정
                if not out_kor.empty:
                    cols = out_kor.columns.tolist()
                    cols[0] = "검색스타일"
                    out_kor.columns = cols

                # 결과 너무 많으면 제한
                if len(out_kor) > 200:
                    st.warning(f"결과가 {len(out_kor)}개입니다. (상위 200개만 표시) 더 구체적으로 입력해 주세요.")
                    out_kor = out_kor.head(200)

                st.dataframe(out_kor, use_container_width=True)
