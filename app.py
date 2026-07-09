import streamlit as st

from common import (
    CHILD_THEME,
    apply_style,
    family_management_ui,
    format_phone,
    get_user_name,
    install_clear_cache_shortcut_guard,
    install_phone_input_guard,
    load_logs_for_user,
    load_parents_i_help,
    show_auth,
    show_log_summary,
)

st.set_page_config(page_title="이음이 자녀 대시보드", page_icon="🔗", layout="wide")

if "dashboard_user" not in st.session_state:
    st.session_state.dashboard_user = None


def logout():
    st.session_state.dashboard_user = None
    st.rerun()


def show_child_dashboard():
    install_phone_input_guard()
    install_clear_cache_shortcut_guard()

    user = st.session_state.dashboard_user
    apply_style(
        "이음이 자녀 대시보드",
        f"{user.get('name','사용자')}님, 부모님의 디지털 사용 기록을 확인하세요",
        theme="child",
        badge="자녀용",
    )

    st.markdown(
        """
<div class='hero-card'>
    <div class='big-action'>📋 부모님 기록 보기</div>
    <div class='big-action secondary'>👨‍👩‍👧 가족 연결 관리</div>
    <div class='big-action light'>👤 내 기록 보기</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(
            f"<div class='small-note'><b>내 번호:</b> {format_phone(user.get('phone',''))}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("로그아웃"):
            logout()

    tab_parents, tab_family, tab_my = st.tabs(["👵 부모님 기록", "👨‍👩‍👧 가족 관리", "📁 내 기록"])

    with tab_parents:
        links = load_parents_i_help(user["id"])
        st.markdown("### 내가 도와주는 부모님")

        if not links:
            st.markdown(
                """
<div class='guide-card'>
아직 연결된 부모님이 없습니다.<br>
<b>가족 관리</b> 탭에서 부모님 전화번호를 입력해 연결 요청을 보내세요.
</div>
""",
                unsafe_allow_html=True,
            )
        else:
            labels = []
            id_map = {}
            for link in links:
                parent_id = link.get("caree_user_id")
                label = f"{link.get('relation_label') or '부모님'} — {get_user_name(parent_id, link.get('caree_phone',''))}"
                labels.append(label)
                id_map[label] = parent_id

            selected = st.radio("기록을 볼 가족 선택", labels, horizontal=True)
            parent_id = id_map.get(selected)
            if parent_id:
                st.markdown(f"## {selected} 기록")
                show_log_summary(load_logs_for_user(parent_id))

    with tab_family:
        family_management_ui(user, "dash_family")

    with tab_my:
        st.markdown("### 내 기록")
        show_log_summary(load_logs_for_user(user["id"]))


if st.session_state.dashboard_user is None:
    show_auth(
        "dashboard_user",
        title="이음이 자녀 대시보드",
        subtitle="부모님의 디지털 사용 기록을 함께 확인하세요",
        theme="child",
        badge="자녀용",
    )
else:
    show_child_dashboard()
