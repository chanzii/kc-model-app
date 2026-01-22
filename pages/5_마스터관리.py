import streamlit as st
import pandas as pd
from lib.data_io import load_df, save_df_and_commit
from lib.audit import log

st.title("⚙️ 마스터 관리 (관리자)")

# 관리자 체크
if st.session_state.get("is_admin") is not True:
    st.warning("관리자 모드에서만 접근 가능합니다. (사이드바에서 관리자 모드 ON)")
    st.stop()

user = st.session_state.get("user_name", "unknown")

tab1, tab2, tab3 = st.tabs(["생산거점", "품목군", "조성섬유"])

def _ensure_active_col(df: pd.DataFrame, key_col: str):
    if df.empty:
        df = pd.DataFrame(columns=[key_col, "active"])
    if "active" not in df.columns:
        df["active"] = "TRUE"
    df["active"] = df["active"].replace("", "TRUE")
    return df

# --------------------------
# 생산거점
# --------------------------
with tab1:
    df = _ensure_active_col(load_df("hubs"), "hub")
    st.dataframe(df, use_container_width=True)

    st.markdown("#### 새 생산거점 추가")
    new_val = st.text_input("생산거점", placeholder="예: 필리핀 1공장", key="new_hub")
    if st.button("추가", key="add_hub"):
        v = new_val.strip()
        if not v:
            st.warning("값을 입력하세요.")
        elif (df["hub"] == v).any():
            st.warning("이미 존재합니다.")
        else:
            df = pd.concat([df, pd.DataFrame([{"hub": v, "active": "TRUE"}])], ignore_index=True)
            save_df_and_commit("hubs", df, commit_msg="master hubs update")
            log("MASTER_ADD_HUB", user, v)
            st.success("추가 완료")

    st.markdown("#### 활성/비활성 토글")
    sel = st.selectbox("대상", options=[""] + df["hub"].tolist(), key="sel_hub")
    if sel:
        cur = df[df["hub"] == sel].iloc[0]["active"]
        st.write(f"현재: {cur}")
        if st.button("토글(활성↔비활성)", key="tog_hub"):
            idx = df[df["hub"] == sel].index[0]
            df.at[idx, "active"] = "FALSE" if str(cur).upper() == "TRUE" else "TRUE"
            save_df_and_commit("hubs", df, commit_msg="master hubs toggle")
            log("MASTER_TOGGLE_HUB", user, f"{sel} -> {df.at[idx,'active']}")
            st.success("변경 완료")

# --------------------------
# 품목군
# --------------------------
with tab2:
    df = _ensure_active_col(load_df("cats"), "category")
    st.dataframe(df, use_container_width=True)

    st.markdown("#### 새 품목군 추가")
    new_val = st.text_input("품목군", placeholder="예: 내의류", key="new_cat")
    if st.button("추가", key="add_cat"):
        v = new_val.strip()
        if not v:
            st.warning("값을 입력하세요.")
        elif (df["category"] == v).any():
            st.warning("이미 존재합니다.")
        else:
            df = pd.concat([df, pd.DataFrame([{"category": v, "active": "TRUE"}])], ignore_index=True)
            save_df_and_commit("cats", df, commit_msg="master categories update")
            log("MASTER_ADD_CATEGORY", user, v)
            st.success("추가 완료")

    st.markdown("#### 활성/비활성 토글")
    sel = st.selectbox("대상", options=[""] + df["category"].tolist(), key="sel_cat")
    if sel:
        cur = df[df["category"] == sel].iloc[0]["active"]
        st.write(f"현재: {cur}")
        if st.button("토글(활성↔비활성)", key="tog_cat"):
            idx = df[df["category"] == sel].index[0]
            df.at[idx, "active"] = "FALSE" if str(cur).upper() == "TRUE" else "TRUE"
            save_df_and_commit("cats", df, commit_msg="master categories toggle")
            log("MASTER_TOGGLE_CATEGORY", user, f"{sel} -> {df.at[idx,'active']}")
            st.success("변경 완료")

# --------------------------
# 조성섬유
# --------------------------
with tab3:
    df = load_df("fibers")
    if df.empty:
        df = pd.DataFrame(columns=["fiber", "sort_order", "active"])
    if "active" not in df.columns:
        df["active"] = "TRUE"
    if "sort_order" not in df.columns:
        df["sort_order"] = "9999"
    df["active"] = df["active"].replace("", "TRUE")

    st.dataframe(df, use_container_width=True)

    st.markdown("#### 새 조성섬유 추가")
    c1, c2 = st.columns(2)
    with c1:
        new_f = st.text_input("섬유명", placeholder="예: 레이온", key="new_fiber")
    with c2:
        new_o = st.number_input("정렬순서(sort_order)", min_value=1, value=50, step=1, key="new_order")

    if st.button("추가", key="add_fiber"):
        nf = new_f.strip()
        if not nf:
            st.warning("섬유명을 입력하세요.")
        elif (df["fiber"] == nf).any():
            st.warning("이미 존재합니다.")
        else:
            df = pd.concat([df, pd.DataFrame([{
                "fiber": nf,
                "sort_order": str(int(new_o)),
                "active": "TRUE"
            }])], ignore_index=True)
            save_df_and_commit("fibers", df, commit_msg="master fibers update")
            log("MASTER_ADD_FIBER", user, f"{nf} order={int(new_o)}")
            st.success("추가 완료")

    st.markdown("#### 활성/비활성 토글")
    sel = st.selectbox("대상", options=[""] + df["fiber"].tolist(), key="sel_fiber")
    if sel:
        cur = df[df["fiber"] == sel].iloc[0]["active"]
        st.write(f"현재: {cur}")
        if st.button("토글(활성↔비활성)", key="tog_fiber"):
            idx = df[df["fiber"] == sel].index[0]
            df.at[idx, "active"] = "FALSE" if str(cur).upper() == "TRUE" else "TRUE"
            save_df_and_commit("fibers", df, commit_msg="master fibers toggle")
            log("MASTER_TOGGLE_FIBER", user, f"{sel} -> {df.at[idx,'active']}")
            st.success("변경 완료")
