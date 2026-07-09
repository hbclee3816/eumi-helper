import streamlit as st
from common import *

st.set_page_config(page_title="이음이 부모님용", page_icon="🔗", layout="centered")

if "eumi_user" not in st.session_state:
    st.session_state.eumi_user = None


def logout():
    st.session_state.eumi_user = None
    st.rerun()


def show_parent_main():
    install_phone_input_guard()
    install_clear_cache_shortcut_guard()

    user = st.session_state.eumi_user
    apply_style(
        "이음이 부모님용",
        f"{user.get('name','사용자')}님, 어려운 화면은 사진으로 물어보세요",
        theme="parent",
        badge="부모님용",
    )

    st.markdown(
        """
<div class='hero-card'>
    <div class='big-action'>📷 사진으로 물어보기</div>
    <div class='big-action secondary'>🕘 지난 기록 보기</div>
    <div class='big-action light'>👨‍👩‍👧 가족 연결하기</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(
            f"<div class='small-note'><b>내 번호:</b> {format_phone(user.get('phone',''))}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        if st.button("로그아웃"):
            logout()

    tab_help, tab_history, tab_family = st.tabs(["📷 도움받기", "📁 내 기록", "👨‍👩‍👧 가족 연결"])

    with tab_help:
        st.markdown("#### 📷 막히는 화면 사진을 올려주세요")
        st.markdown(
            """
<div class='guide-card'>
키오스크, 병원 앱, 은행 앱, 기차 예매 화면 등<br>
<b>막히는 화면을 사진으로 찍어서 올려주세요.</b><br>
이전에 비슷한 질문이 있으면 같이 참고해서 알려드립니다.
</div>
""",
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader(
            "사진 선택",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        question = st.text_input(
            "질문",
            value="이 화면에서 다음에 뭘 누르면 되나요?",
            key="help_question",
        )

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="업로드된 화면", use_container_width=True)

            if st.button("✨ AI에게 물어보기"):
                with st.spinner("AI가 화면을 분석하고 있어요..."):
                    try:
                        result = classify_and_answer(image, question, load_logs_for_user(user["id"]))
                        save_usage_log(user["id"], question, result, True)

                        st.markdown("#### 📣 AI 답변")
                        st.markdown(
                            f"<div class='answer-card'>{result.get('answer')}</div>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f"""
<div class='folder-card'>
<b>자동 분류</b><br>
📁 {result.get('category')} &gt; {result.get('place_name')}<br>
하려는 일: {result.get('task_name')}
</div>
""",
                            unsafe_allow_html=True,
                        )
                    except Exception as e:
                        show_error(e, "오류가 발생했어요")
        else:
            st.markdown("<div class='guide-card'>먼저 사진을 올려주세요.</div>", unsafe_allow_html=True)

    with tab_history:
        st.markdown("### 내가 물어본 기록")
        show_log_summary(load_logs_for_user(user["id"]))

    with tab_family:
        family_management_ui(user, "main_family")


if st.session_state.eumi_user is None:
    show_auth(
        "eumi_user",
        title="이음이 부모님용",
        subtitle="어려운 화면, 사진 찍어서 물어보세요",
        theme="parent",
        badge="부모님용",
    )
else:
    show_parent_main()
