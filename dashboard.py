import streamlit as st

from common import (
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
if "child_view" not in st.session_state:
    st.session_state.child_view = "parents"


def logout():
    st.session_state.dashboard_user = None
    st.session_state.child_view = "parents"
    st.rerun()


def select_child_view(view: str):
    st.session_state.child_view = view
    st.rerun()


def render_child_action_buttons():
    st.markdown(
        """
<div class='hero-card'>
    <div class='small-note'><b>확인할 화면을 선택하세요.</b> 로그인 후에는 아래 버튼이 실제 화면 이동 버튼으로 작동합니다.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("📋 부모님 기록 보기", key="go_parent_records", use_container_width=True):
        select_child_view("parents")
    if st.button("👨‍👩‍👧 가족 연결 관리", key="go_family_manage", use_container_width=True):
        select_child_view("family")
    if st.button("👤 내 기록 보기", key="go_my_records", use_container_width=True):
        select_child_view("my")


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

    render_child_action_buttons()

    col_a, col_b = st.columns([4, 1])
    with col_a:
        st.markdown(
            f"<div class='small-note'><b>내 번호:</b> {format_phone(user.get('phone',''))}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("로그아웃"):
            logout()

    view = st.session_state.child_view

    if view == "parents":
        links = load_parents_i_help(user["id"])
        st.markdown("### 👵 부모님 기록 보기")

        if not links:
            st.markdown(
                """
<div class='guide-card'>
아직 연결된 부모님이 없습니다.<br>
<b>가족 연결 관리</b> 버튼을 눌러 부모님 전화번호를 입력해 연결 요청을 보내세요.
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

    elif view == "family":
        st.markdown("### 👨‍👩‍👧 가족 연결 관리")
        family_management_ui(user, "dash_family")

    elif view == "my":
        st.markdown("### 📁 내 기록 보기")
        show_log_summary(load_logs_for_user(user["id"]))


if st.session_state.dashboard_user is None:
    show_auth(
        "dashboard_user",
        title="이음이 자녀 대시보드",
        subtitle="먼저 로그인하거나 처음 사용에서 가입해주세요",
        theme="child",
        badge="자녀용",
    )
else:
    show_child_dashboard()
