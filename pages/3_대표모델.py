import streamlit as st
import pandas as pd
from datetime import datetime
from lib.data_io import load_df, save_df_and_commit
from lib.rules import normalize_fiber_key, expiry_status
from lib.audit import log

st.title("📑 대표모델")

rep = load_df("rep")
hubs = load_df("hubs")
cats = load_df("cats")
fibers = load_df("fibers")

# 활성 마스터만
active_hubs = hubs[hubs.get("active","").str.upper() == "TRUE"]["hub"].tolist() if not hubs.empty else []
active_cats = cats[cats.get("active","").str.upper() == "TRUE"]["category"].tolist() if not cats.empty else []

active_fibers_df = fibers[fibers.get("active","").str.upper() == "TRUE"] if not fibers.empty else pd.DataFrame(columns=["fiber","sort_order"])
active_fibers = active_fibers_df["fiber"].tolist()

# 섬유 정렬 맵
fiber_order = {}
if not active_fibers_df.empty:
    for _, r in active_fibers_df.iterrows():
        try:
            fiber_order[r["fiber"]] = int(r.get("sort_order", "9999") or 9999)
        except Exception:
            fiber_order[r["fiber"]] = 9999

# -----------------------------
# 대표모델 목록
# -----------------------------
st.subheader("대표모델 목록")

if rep.empty:
    st.info("대표모델 데이터가 없습니다.")
else:
    view = rep.copy()
    badges = []
    for _, r in view.iterrows():
        icon, msg = expiry_status(r.get("expiry_date",""))
        badges.append(f"{icon} {msg}")
    view["status"] = badges

    st.dataframe(
        view[["rep_id","hub","category","fiber_key","kc_no","cert_date","expiry_date","status","memo","updated_by","updated_at"]],
        use_container_width=True
    )

st.markdown("---")

# -----------------------------
# 등록/수정 (관리자)
# -----------------------------
st.subheader("대표모델 등록/수정 (관리자)")

if st.session_state.get("is_admin") is not True:
    st.warning("관리자 모드에서만 등록/수정이 가능합니다. (사이드바에서 관리자 모드 ON)")
    st.stop()

if not active_hubs or not active_cats or not active_fibers:
    st.error("마스터(생산거점/품목군/조성섬유)를 먼저 등록하세요. (마스터관리 페이지)")
    st.stop()

mode = st.radio("모드", ["새로 등록", "기존 수정"], horizontal=True)

edit_rep_id = None
default = {
    "hub": active_hubs[0],
    "cat": active_cats[0],
    "fibers": [],
    "kc_no": "",
    "cert_date": "",
    "expiry_date": "",
    "memo": "",
}

if mode == "기존 수정":
    if rep.empty:
        st.info("수정할 대표모델이 없습니다.")
        st.stop()

    rep["label"] = rep["rep_id"] + " | " + rep["hub"] + " | " + rep["category"] + " | " + rep["fiber_key"]
    label = st.selectbox("수정할 대표모델 선택", options=rep["label"].tolist())
    edit_rep_id = label.split(" | ")[0].strip()

    row = rep[rep["rep_id"] == edit_rep_id].iloc[0].to_dict()
    default["hub"] = row.get("hub", default["hub"])
    default["cat"] = row.get("category", default["cat"])
    # fiber_key -> 멀티선택 기본값으로 풀기
    default["fibers"] = [x for x in (row.get("fiber_key","").split("|") if row.get("fiber_key","") else []) if x]
    default["kc_no"] = row.get("kc_no","")
    default["cert_date"] = row.get("cert_date","")
    default["expiry_date"] = row.get("expiry_date","")
    default["memo"] = row.get("memo","")

with st.form("rep_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        hub = st.selectbox("생산거점", options=active_hubs, index=active_hubs.index(default["hub"]) if default["hub"] in active_hubs else 0)
    with col2:
        cat = st.selectbox("품목군", options=active_cats, index=active_cats.index(default["cat"]) if default["cat"] in active_cats else 0)
    with col3:
        selected = st.multiselect("조성섬유(정확히 일치)", options=active_fibers, default=[f for f in default["fibers"] if f in active_fibers])

    kc_no = st.text_input("KC 안전확인번호", value=default["kc_no"], placeholder="예: KC-XXXX-XXXX")
    cert_date = st.text_input("인증일 (YYYY-MM-DD)", value=default["cert_date"], placeholder="예: 2024-06-01")
    expiry_date = st.text_input("유효기간 (YYYY-MM-DD)", value=default["expiry_date"], placeholder="예: 2026-05-30")
    memo = st.text_area("메모", value=default["memo"], height=80)

    submitted = st.form_submit_button("저장", type="primary")

if submitted:
    user = st.session_state.get("user_name","unknown")

    if not selected:
        st.error("조성섬유를 선택하세요.")
        st.stop()

    fiber_key = normalize_fiber_key(selected, fiber_order)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if rep.empty:
        rep = pd.DataFrame(columns=["rep_id","hub","category","fiber_key","kc_no","cert_date","expiry_date","memo","updated_at","updated_by"])

    # (중요) 동일 조건 유니크 체크: 다른 rep_id가 이미 같은 조합이면 막기
    conflict = rep[(rep["hub"] == hub) & (rep["category"] == cat) & (rep["fiber_key"] == fiber_key)]
    if mode == "기존 수정" and edit_rep_id:
        conflict = conflict[conflict["rep_id"] != edit_rep_id]

    if not conflict.empty:
        st.error("❌ 같은 조건(생산거점+품목군+조성) 대표모델이 이미 존재합니다. (중복 불가)")
        st.stop()

    if mode == "기존 수정" and edit_rep_id:
        idx = rep[rep["rep_id"] == edit_rep_id].index[0]
        rep.at[idx, "hub"] = hub
        rep.at[idx, "category"] = cat
        rep.at[idx, "fiber_key"] = fiber_key
        rep.at[idx, "kc_no"] = kc_no
        rep.at[idx, "cert_date"] = cert_date
        rep.at[idx, "expiry_date"] = expiry_date
        rep.at[idx, "memo"] = memo
        rep.at[idx, "updated_at"] = now
        rep.at[idx, "updated_by"] = user

        save_df_and_commit("rep", rep, commit_msg=f"update rep_model {edit_rep_id}")
        log("REP_UPDATE", user, f"{edit_rep_id} {hub}/{cat}/{fiber_key} KC={kc_no}")
        st.success(f"✅ 수정 완료: {edit_rep_id}")

    else:
        # 새 rep_id 생성
        existing = rep["rep_id"].tolist()
        nums = []
        for rid in existing:
            if isinstance(rid, str) and rid.startswith("RM"):
                try:
                    nums.append(int(rid[2:]))
                except Exception:
                    pass
        nxt = (max(nums) + 1) if nums else 1
        rep_id = f"RM{nxt:04d}"

        new_row = {
            "rep_id": rep_id,
            "hub": hub,
            "category": cat,
            "fiber_key": fiber_key,
            "kc_no": kc_no,
            "cert_date": cert_date,
            "expiry_date": expiry_date,
            "memo": memo,
            "updated_at": now,
            "updated_by": user,
        }
        rep = pd.concat([rep, pd.DataFrame([new_row])], ignore_index=True)
        save_df_and_commit("rep", rep, commit_msg=f"add rep_model {rep_id}")
        log("REP_ADD", user, f"{rep_id} {hub}/{cat}/{fiber_key} KC={kc_no}")
        st.success(f"✅ 등록 완료: {rep_id}")
