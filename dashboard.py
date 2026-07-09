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

st.set_page_config(page_title="이음이 자녀용", page_icon="🔗", layout="centered")

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



def render_child_visual_card():
    """부모용 메인 카드와 같은 구조로 만든 자녀용 시안형 카드입니다."""
    st.markdown(
        """
<style>
.child-main-card {
    background: linear-gradient(135deg, #FDFEFF 0%, #EEF7FF 58%, #DFF1FF 100%);
    border: 2px solid #CFE0F2;
    border-radius: 28px;
    padding: 1.6rem 1.7rem;
    margin: 1rem auto 1.4rem;
    box-shadow: 0 18px 45px rgba(9, 61, 120, .12);
    position: relative;
    overflow: hidden;
}
.child-main-card:before {
    content: "";
    position: absolute;
    width: 260px;
    height: 260px;
    right: -90px;
    bottom: -90px;
    border-radius: 50%;
    background: rgba(255,255,255,.48);
}
.child-main-grid {
    display: grid;
    grid-template-columns: 1.22fr .78fr;
    gap: 1.1rem;
    align-items: center;
    position: relative;
    z-index: 1;
}
.child-badge {
    display: inline-flex;
    background: #0A3D78;
    color: #fff;
    border-radius: 14px;
    padding: .35rem .8rem;
    font-size: 1rem;
    font-weight: 900;
    margin-bottom: .75rem;
}
.child-card-title {
    font-size: 2.25rem;
    font-weight: 900;
    color: #0A3D78;
    letter-spacing: -0.04em;
    margin: .15rem 0 .35rem;
    white-space: nowrap;
    word-break: keep-all;
}
.child-headline {
    font-size: 1.55rem;
    font-weight: 900;
    color: #0F1C33;
    line-height: 1.36;
    margin: .35rem 0;
    word-break: keep-all;
}
.child-copy {
    font-size: 1.02rem;
    color: #536273;
    font-weight: 650;
    line-height: 1.65;
    margin: .35rem 0 1rem;
}
.child-action {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-radius: 18px;
    padding: .85rem 1rem;
    margin: .65rem 0;
    font-size: 1.22rem;
    font-weight: 900;
    color: #fff;
    box-shadow: 0 8px 18px rgba(0,0,0,.10);
}
.child-action .left {
    display: flex;
    gap: .75rem;
    align-items: center;
}
.child-action .ico {
    width: 2.35rem;
    height: 2.35rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    background: rgba(255,255,255,.22);
}
.child-action.one { background: #0A3D78; }
.child-action.two { background: #2F7DB7; }
.child-action.three { background: #52B5BA; }
.child-arrow {
    font-size: 2rem;
    line-height: 1;
}
.child-ill {
    background: #DCEFFF;
    border-radius: 26px;
    min-height: 215px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4.2rem;
}
.child-note {
    text-align: center;
    color: #536273;
    font-size: 1.02rem;
    font-weight: 800;
    margin-top: .45rem;
}
@media (max-width: 900px) {
    .child-main-grid { grid-template-columns: 1fr; }
    .child-ill { min-height: 130px; font-size: 3rem; }
    .child-card-title { font-size: 1.85rem; white-space: normal; }
}
</style>

<div class='child-main-card'>
  <div class='child-main-grid'>
    <div>
      <div class='child-badge'>👤 자녀용</div>
      <div class='child-card-title'>🔗 이음이 자녀용</div>
      <div class='child-headline'>부모님의 디지털 사용 기록을<br>함께 확인하세요</div>
      <div class='child-copy'>어디에서 자주 어려워하시는지 보고,<br>가족 연결도 관리할 수 있어요.</div>

      <div class='child-action one'>
        <span class='left'><span class='ico'>📋</span>부모님 기록 보기</span>
        <span class='child-arrow'>›</span>
      </div>
      <div class='child-action two'>
        <span class='left'><span class='ico'>👨‍👩‍👧</span>가족 연결 관리</span>
        <span class='child-arrow'>›</span>
      </div>
      <div class='child-action three'>
        <span class='left'><span class='ico'>👤</span>내 기록 보기</span>
        <span class='child-arrow'>›</span>
      </div>
    </div>

    <div>
      <div class='child-ill'>👨‍💻📊👪</div>
      <div class='child-note'>기록 확인 중심</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_child_action_buttons():
    st.markdown(
        """
<div class='hero-card'>
    <div class='small-note'><b>원하는 기능을 눌러주세요.</b> 로그인 후에는 아래 버튼이 실제 화면 이동 버튼으로 작동합니다.</div>
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
        "이음이 자녀용",
        f"{user.get('name','사용자')}님, 부모님의 디지털 사용 기록을 확인하세요",
        theme="child",
        badge="자녀용",
    )

    render_child_visual_card()

    render_child_action_buttons()

    col_a, col_b = st.columns([3, 1])
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
        title="이음이 자녀용",
        subtitle="먼저 로그인하거나 처음 사용에서 가입해주세요",
        theme="child",
        badge="자녀용",
    )
else:
    show_child_dashboard()
