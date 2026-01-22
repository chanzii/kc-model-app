import streamlit as st
import pandas as pd
from datetime import datetime
from lib.data_io import load_df, save_df_and_commit
from lib.audit import log

st.title("🔗 동일모델(STYLENO) 연결")

rep = load_df("rep")
style = load_df("style")

if rep.empty:
    st.info("대표모델이 없습니다. 먼저 대표모델을 등록하세요.")
    st.stop()

# 대표모델 선택 라벨 만들기
rep = rep.copy()
rep["label"] = rep["rep_id"] + " | " + rep["hub"] + " | " + rep["category"] + " | " + rep["fiber_key"]

selected_label = st.selectbox("연결할 대표모델 선택", options=rep["label"].tolist())
target_rep_id = selected_label.split(" | ")[0].strip()

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
    user = st.session_state.get("user_name","unknown")

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
        style = pd.DataFrame(columns=["style_no","rep_id","linked_at","linked_by","memo"])

    # 현재 매핑 dict
    existing = {r["style_no"]: r for _, r in style.iterrows()}

    new_ok = []
    dup = []  # (style_no, current_rep_id)

    for s in tokens:
        if s in existing and existing[s].get("rep_id","") and existing[s]["rep_id"] != target_rep_id:
            dup.append((s, existing[s]["rep_id"]))
        else:
            new_ok.append(s)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    changed = False

    # 신규/동일 rep 연결은 즉시 반영
    for s in new_ok:
        if s in existing:
            # 이미 같은 rep에 연결된 경우는 패스
            if existing[s].get("rep_id","") == target_rep_id:
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

    rep_lookup = {r["rep_id"]: r for _, r in rep.iterrows()}
    style_df = st.session_state.get("pending_style_df", style)
    target_rep_id = st.session_state.get("target_rep_id", "")

    decisions = {}
    for s, cur_rep_id in dup:
        cur = rep_lookup.get(cur_rep_id, {})
        st.markdown(
            f"**{s}**  \n"
            f"- 현재 연결: `{cur_rep_id}` ({cur.get('hub','')} / {cur.get('category','')} / {cur.get('fiber_key','')})"
        )
        decisions[s] = st.radio(
            f"{s} 처리",
            options=["그대로 두기(스킵)", "현재 대표모델로 이동(재연결)"],
            key=f"dec_{s}",
            horizontal=True
        )

    st.info("이동(재연결)이 포함되면, 실수 방지를 위해 아래에 `MOVE`를 입력해야 적용됩니다.")
    confirm = st.text_input("확인 입력", placeholder="MOVE")

    if st.button("중복 처리 적용"):
        user = st.session_state.get("user_name","unknown")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        any_move = any(v.startswith("현재 대표모델로 이동") for v in decisions.values())
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
