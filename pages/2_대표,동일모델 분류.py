import streamlit as st
import pandas as pd
from lib.data_io import load_df
from lib.rules import expiry_status

st.title("📂 폴더 탐색")

rep = load_df("rep")
hubs = load_df("hubs")
cats = load_df("cats")
fibers = load_df("fibers")
style_map = load_df("style")

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

    df_display["KC 링크"] = df_display["인증번호"].apply(
        lambda x: f"https://www.safetykorea.kr/release/certDetail?certNum={x}"
        if pd.notna(x) and str(x).strip() and str(x) != "nan" else None
    )
    display_cols = [
        "스타일",
        "생산처",
        "분류",
        "조성섬유",
        "인증번호",
        "KC 링크",
        "신고일",
        "만료일",
        "잔여기간",
        "등록",
        "등록일",
    ]
    display_cols = [c for c in display_cols if c in df_display.columns]
    return df_display[display_cols]

def show_linked_styles_for_rep(rep_df: pd.DataFrame):
    """
    rep_df: 현재 화면에서 필터된 대표모델 df (rep_id 포함)
    """
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

    st.markdown("### 🔗 선택한 대표모델에 연결된 동일모델(STYLENO)")

    rid = st.selectbox(
        "대표모델 선택",
        options=rep_df["rep_id"].tolist(),
        format_func=rep_label,
        key="folder_rep_link_view_selectbox",
    )

    linked = style_map[style_map["rep_id"] == rid].copy()
    if "style_no" in linked.columns:
        linked["style_no"] = linked["style_no"].astype(str)
        linked = linked.sort_values("style_no")

    st.write(f"연결된 동일모델: **{len(linked)}개**")

    if linked.empty:
        st.info("연결된 동일모델이 없습니다.")
        return

    st.dataframe(linked[["style_no"]].rename(columns={"style_no": "STYLENO"}), use_container_width=True)
    st.text_area("복사용(STYLENO 줄바꿈)", "\n".join(linked["style_no"].tolist()), height=140, key="folder_rep_link_view_copy")

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
    st.dataframe(
        make_korean_table_from_rep(df),
        column_config={"KC 링크": st.column_config.LinkColumn("KC 링크", display_text="🔗")},
        use_container_width=True,
    )
    show_linked_styles_for_rep(df)
