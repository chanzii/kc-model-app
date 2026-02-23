import streamlit as st
import pandas as pd
from datetime import datetime
from lib.data_io import load_df, save_df_and_commit
from lib.audit import log

st.title("🔗 동일모델(STYLENO) 연결")

rep = load_df("rep")
style = load_df("style")

# 호환: rep_style_no 없으면 추가
if not rep.empty and "rep_style_no" not in rep.columns:
    rep["rep_style_no"] = ""

if rep.empty:
    st.info("대표모델이 없습니다. 먼저 대표모델을 등록하세요.")
    st.stop()

# rep_id -> row lookup
rep = rep.copy()
rep_lookup = {r["rep_id"]: r for _, r in rep.iterrows()}

def label_for_rep_id(rep_id: str) -> str:
    r = rep_lookup.get(rep_id, {})
    rep_style = (r.get("rep_style_no") or "").strip()
    hub = (r.get("hub") or "").strip()
    cat = (r.get("category") or "").strip()
    fiber = (r.get("fiber_key") or "").strip()
    kc = (r.get("kc_no") or "").strip()

    if not rep_style:
        rep_style = "(대표스타일없음)"
    if not kc:
        kc = "(KC없음)"

    # ✅ RM0001 같은 rep_id는 화면에 안 보이게 하고,
    # ✅ 대표스타일 | 생산처 | 분류 | 조성 | KC만 보여줌
    return f"{rep_style} | {hub} | {cat} | {fiber} | {kc}"
# ✅ 동일모델 추가/연결은 관리자만
if st.session_state.get("is_admin") is not True:
    st.warning("🔒 동일모델 추가/연결은 관리자만 가능합니다. 사이드바에서 관리자 모드를 켜주세요.")
    st.stop()
st.markdown("### 연결할 대표모델 선택")

# ----------------------------
# ✅ 조성섬유(fiber_key)로 대표모델 목록 필터링
# ----------------------------
rep_for_filter = rep.copy()
rep_for_filter["fiber_key"] = rep_for_filter["fiber_key"].fillna("").astype(str).str.strip()

fiber_options = sorted([x for x in rep_for_filter["fiber_key"].unique().tolist() if x])

fiber_filter = st.selectbox(
    "조성섬유로 필터(선택 시 대표모델 목록이 줄어듭니다)",
    options=["(전체)"] + fiber_options,
    index=0
)

if fiber_filter != "(전체)":
    rep_filtered = rep_for_filter[rep_for_filter["fiber_key"] == fiber_filter].copy()
else:
    rep_filtered = rep_for_filter

rep_ids = rep_filtered["rep_id"].tolist()

st.caption(f"대표모델 {len(rep_ids)}개 표시 중 (전체 {len(rep_for_filter)}개)")
# ----------------------------

# ✅ 옵션은 rep_id로 갖고, 화면 표시만 label로 바꿈 (파싱 필요 없음)
target_rep_id = st.selectbox(
    "대표모델",
    options=rep_ids,
    format_func=label_for_rep_id
)

st.markdown("### STYLENO 여러 개 붙여넣기")
st.caption("줄바꿈 또는 쉼표로 구분 가능. 예: ABC12345, ABC12346 ...")

raw = st.text_area("STYLENO 입력", height=180, placeholder="ABC12345\nABC12346\nABC12347")

# 세션 초기화
if "dup_items" not in st.session_state:
    st.session_state["dup_items"] = []
if "pending_style_df" not in st.session_state:
    st.session_state["pending_style_df"] = None
if "target_rep_id" not in st.session_state:
    st.session_state["target_rep_id"] = ""

if st.button("추가/연결", type="primary"):
    user = st.session_state.get("user_name", "unknown")

    if not raw.strip():
        st.warning("입력값이 없습니다.")
        st.stop()

    # 파싱: 콤마/줄바꿈 처리
    tokens = []
    for part in raw.replace(",", "\n").split("\n"):
        t = part.strip()
        if t:
            tokens.append(t)

    # 입력 내부 중복 제거
    tokens = list(dict.fromkeys(tokens))

    # style_map 초기화
    if style.empty:
        style = pd.DataFrame(columns=["style_no", "rep_id", "linked_at", "linked_by", "memo"])

    # 현재 매핑 dict
    existing = {r["style_no"]: r for _, r in style.iterrows()}

    new_ok = []
    dup = []  # (style_no, current_rep_id)

    for s in tokens:
        if s in existing and existing[s].get("rep_id", "") and existing[s]["rep_id"] != target_rep_id:
            dup.append((s, existing[s]["rep_id"]))
        else:
            new_ok.append(s)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changed = False

    # 신규/동일 rep 연결은 즉시 반영
    for s in new_ok:
        if s in existing:
            # 이미 같은 rep에 연결된 경우는 패스
            if existing[s].get("rep_id", "") == target_rep_id:
                continue
            idx = style[style["style_no"] == s].index[0]
            style.at[idx, "rep_id"] = target_rep_id
            style.at[idx, "linked_at"] = now
            style.at[idx, "linked_by"] = user
            changed = True
        else:
            row = {"style_no": s, "rep_id": target_rep_id, "linked_at": now, "linked_by": user, "memo": ""}
            style = pd.concat([style, pd.DataFrame([row])], ignore_index=True)
            changed = True

    # 중복 처리 위해 세션에 저장
    st.session_state["dup_items"] = dup
    st.session_state["target_rep_id"] = target_rep_id
    st.session_state["pending_style_df"] = style

    if changed:
        st.success(f"✅ 신규/동일 연결 {len(new_ok)}개 반영 완료 (중복 제외)")
        log("STYLE_LINK", user, f"target={target_rep_id} count={len(new_ok)}")

    if dup:
        st.warning(f"⚠️ 중복 {len(dup)}개 발견: 아래에서 스킵/이동 선택 필요")
    else:
        # 중복이 없으면 바로 커밋
        save_df_and_commit("style", style, commit_msg=f"style_map link to {target_rep_id}")
        st.success("✅ GitHub 저장 완료")

# ----------------------------
# 중복 처리 (스킵/이동)
# ----------------------------
dup = st.session_state.get("dup_items", [])
if dup:
    st.markdown("---")
    st.subheader("⚠️ 중복 STYLENO 처리 (스킵 / 이동)")

    style_df = st.session_state.get("pending_style_df", style)
    target_rep_id = st.session_state.get("target_rep_id", "")

    decisions = {}
    for s, cur_rep_id in dup:
        cur = rep_lookup.get(cur_rep_id, {})
        cur_style = cur.get("rep_style_no", "")
        cur_kc = cur.get("kc_no", "")
        st.markdown(
            f"**{s}**  \n"
            f"- 현재 연결: **{cur_style}** | {cur.get('hub','')} | {cur.get('category','')} | {cur.get('fiber_key','')} | **{cur_kc}**"
        )
        decisions[s] = st.radio(
            f"{s} 처리",
            options=["그대로 두기(스킵)", "현재 선택한 대표모델로 이동(재연결)"],
            key=f"dec_{s}",
            horizontal=True
        )

    st.info("이동(재연결)이 포함되면, 실수 방지를 위해 아래에 `MOVE`를 입력해야 적용됩니다.")
    confirm = st.text_input("확인 입력", placeholder="MOVE")

    if st.button("중복 처리 적용"):
        user = st.session_state.get("user_name", "unknown")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        any_move = any(v.startswith("현재 선택한 대표모델로 이동") for v in decisions.values())
        if any_move and confirm.strip().upper() != "MOVE":
            st.error("이동(재연결)이 포함되어 있습니다. 확인 입력란에 MOVE를 입력하세요.")
            st.stop()

        moved, skipped = 0, 0
        for s, cur_rep_id in dup:
            choice = decisions[s]
            if choice.startswith("그대로"):
                skipped += 1
                continue

            # 이동: style_map에서 rep_id 변경
            idxs = style_df[style_df["style_no"] == s].index.tolist()
            if idxs:
                idx = idxs[0]
                style_df.at[idx, "rep_id"] = target_rep_id
                style_df.at[idx, "linked_at"] = now
                style_df.at[idx, "linked_by"] = user
            else:
                row = {"style_no": s, "rep_id": target_rep_id, "linked_at": now, "linked_by": user, "memo": ""}
                style_df = pd.concat([style_df, pd.DataFrame([row])], ignore_index=True)
            moved += 1

        save_df_and_commit("style", style_df, commit_msg=f"style_map resolve duplicates to {target_rep_id}")
        log("STYLE_DUP_RESOLVE", user, f"target={target_rep_id} moved={moved} skipped={skipped}")

        st.success(f"✅ 중복 처리 완료 (이동 {moved}, 스킵 {skipped}) + GitHub 저장 완료")

        # 세션 정리
        st.session_state["dup_items"] = []
        st.session_state["pending_style_df"] = style_df

# ----------------------------
# 동일모델(STYLENO) 삭제/해제 (관리자)
# ----------------------------
st.markdown("---")
st.subheader("🗑️ 동일모델(STYLENO) 삭제/해제 (관리자)")

if st.session_state.get("is_admin") is not True:
    st.info("관리자 모드에서만 삭제/해제가 가능합니다.")
else:
    style_df = load_df("style")
    if style_df.empty:
        st.info("동일모델 데이터가 없습니다.")
    else:
        raw_del = st.text_area("삭제/해제할 STYLENO 입력(여러 개 가능)", height=120, placeholder="ABC12345\nABC12346")
        confirm2 = st.text_input("삭제 확인 입력", placeholder="DELETE", key="del_style_confirm")

        if st.button("STYLENO 삭제/해제 실행", type="primary"):
            if confirm2.strip().upper() != "DELETE":
                st.error("삭제 확인 입력란에 DELETE를 입력하세요.")
                st.stop()

            tokens = []
            for part in raw_del.replace(",", "\n").split("\n"):
                t = part.strip()
                if t:
                    tokens.append(t)
            tokens = list(dict.fromkeys(tokens))

            before = len(style_df)
            style_df = style_df[~style_df["style_no"].isin(tokens)].copy()
            after = len(style_df)

            save_df_and_commit("style", style_df, commit_msg=f"delete styles {len(tokens)}")
            st.success(f"✅ 삭제 완료: {before-after}건 제거")
            st.rerun()
