import streamlit as st

def sidebar_user_controls():
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 바로가기")
        st.markdown("🔗 [제품안전정보센터](https://www.safetykorea.kr/release/itemSearch)")
        st.markdown("### 사용자")
        user = st.text_input("사용자명", value=st.session_state.get("user_name", ""))
        st.session_state["user_name"] = user or "unknown"

        st.markdown("---")
        st.markdown("### 관리자 모드")

        if st.session_state.get("is_admin"):
            st.success("관리자 모드 ON")
            if st.button("관리자 모드 OFF"):
                st.session_state["is_admin"] = False
        else:
            pw = st.text_input("관리자 비밀번호", type="password")
            if st.button("관리자 모드 ON"):
                if pw == st.secrets.get("ADMIN_PASS"):
                    st.session_state["is_admin"] = True
                    st.success("관리자 모드 ON")
                else:
                    st.error("비밀번호가 틀렸습니다.")
