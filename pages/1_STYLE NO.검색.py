import streamlit as st
import pandas as pd
from lib.data_io import load_df
from lib.rules import expiry_status

st.title("🔍 STYLE NO 검색")

rep = load_df("rep")
style = load_df("style")

# 호환: rep_style_no 없으면 추가
if not rep.empty and "rep_style_no" not in rep.columns:
    rep["rep_style_no"] = ""

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
        "스타일", "생산처", "분류", "조성섬유",
        "인증번호", "신고일", "만료일", "잔여기간",
        "등록", "등록일"
    ]
    display_cols = [c for c in display_cols if c in df_display.columns]
    return df_display[display_cols]

def show_linked_styles_for_rep(rep_df: pd.DataFrame, title: str = "🔗 선택한 대표모델에 연결된 동일모델(STYLENO)"):
    """
    rep_df: rep_id를 포함한 대표모델 데이터프레임(필터된 결과여도 OK)
    """
    style_map = load_df("style")
    if style_map.empty:
        st.info("동일모델(STYLENO) 연결 데이터가 없습니다.")
        return

    if rep_df is None or rep_df.empty:
        return

    if "rep_id" not in rep_df.columns:
        st.warning("rep_id 컬럼이 없어 동일모델 연결 조회를 할 수 없습니다.")
        return

    rep_df = rep_df.copy()

    rep_lookup = {r["rep_id"]: r for _, r in rep_df.iterrows()}

    def rep_label(rid: str) -> str:
        r = rep_lookup.get(rid, {})
        rep_style = (r.get("rep_style_no") or "").strip() or "(대표스타일없음)"
        hub = (r.get("hub") or "").strip()
        cat = (r.get("category") or "").strip()
        fiber = (r.get("fiber_key") or "").strip()
        kc = (r.get("kc_no") or "").strip() or "(KC없음)"
        return f"{rep_style} | {hub} | {cat} | {fiber} | {kc}"

    st.markdown(f"### {title}")

    rid = st.selectbox(
        "대표모델 선택",
        options=rep_df["rep_id"].tolist(),
        format_func=rep_label,
        key="rep_link_view_selectbox"
    )

    linked = style_map[style_map["rep_id"] == rid].copy()
    if "style_no" in linked.columns:
        linked["style_no"] = linked["style_no"].astype(str)
        linked = linked.sort_values("style_no")

    st.write(f"연결된 동일모델: **{len(linked)}개**")

    if linked.empty:
        st.info("연결된 동일모델이 없습니다.")
        return

    # 표 + 복사용 텍스트
    if "style_no" in linked.columns:
        st.dataframe(linked[["style_no"]].rename(columns={"style_no": "STYLENO"}), use_container_width=True)
        st.text_area("복사용(STYLENO 줄바꿈)", "\n".join(linked["style_no"].tolist()), height=140, key="rep_link_view_copy")
    else:
        st.dataframe(linked, use_container_width=True)

q = st.text_input("검색어", placeholder="예: ABC / ABC12 / 123 등")
mode = st.radio("검색 방식", options=["앞에서 일치(prefix)", "포함(contains)"], horizontal=True)
min_len = 2

if not q or len(q.strip()) < min_len:
    st.caption(f"최소 {min_len}글자 이상 입력하면 검색됩니다.")
    st.stop()

q2 = q.strip().upper()

# ----------------------------
# 1) 대표모델(rep_style_no)에서 검색
# ----------------------------
rep_hit = pd.DataFrame()
if not rep.empty:
    rep_style_upper = rep["rep_style_no"].astype(str).str.upper()
    if mode.startswith("앞에서"):
        rep_hit = rep[rep_style_upper.str.startswith(q2)]
    else:
        rep_hit = rep[rep_style_upper.str.contains(q2, na=False)]

# ----------------------------
# 2) 동일모델(style_no)에서 검색 → rep join
# ----------------------------
style_hit_joined = pd.DataFrame()
if not style.empty:
    s_upper = style["style_no"].astype(str).str.upper()
    if mode.startswith("앞에서"):
        hit_style = style[s_upper.str.startswith(q2)]
    else:
        hit_style = style[s_upper.str.contains(q2, na=False)]

    if not hit_style.empty and not rep.empty:
        style_hit_joined = hit_style.merge(
            rep[["rep_id", "rep_style_no", "hub", "category", "fiber_key", "kc_no", "cert_date", "expiry_date", "memo", "updated_at"]],
            on="rep_id",
            how="left"
        )
        style_hit_joined = style_hit_joined.rename(columns={"style_no": "검색스타일"})

# ----------------------------
# 출력
# ----------------------------
st.markdown("---")

st.subheader("대표모델 결과")
if rep_hit.empty:
    st.info("대표모델에서 일치하는 스타일이 없습니다.")
else:
    st.dataframe(make_korean_table_from_rep(rep_hit), use_container_width=True)
    # ✅ 대표모델 클릭 대신: 선택 → 연결된 동일모델 목록 보기
    show_linked_styles_for_rep(rep_hit)

st.markdown("---")

st.subheader("동일모델(STYLENO) 결과")
if style_hit_joined.empty:
    st.info("동일모델(STYLENO)에서 결과가 없습니다.")
else:
    df = style_hit_joined.copy()

    # 잔여기간 계산 + 한글 컬럼 변환(대표모델 표 재사용)
    df_rep_like = df.rename(columns={"검색스타일": "rep_style_no"})  # 임시로 '스타일' 칼럼 자리에 넣기
    out_kor = make_korean_table_from_rep(df_rep_like)

    # ✅ 헤더 교정: 1열=검색스타일, 2열(원래 스타일)=대표스타일
    if not out_kor.empty:
        cols = out_kor.columns.tolist()
        if len(cols) >= 1:
            cols[0] = "검색스타일"
        if len(cols) >= 2 and cols[1] == "스타일":
            cols[1] = "대표스타일"
        out_kor.columns = cols

    if len(out_kor) > 200:
        st.warning(f"결과가 {len(out_kor)}개입니다. (상위 200개만 표시) 더 구체적으로 입력해 주세요.")
        out_kor = out_kor.head(200)

    st.dataframe(out_kor, use_container_width=True)

  
