import os
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="이음이 — 자녀 대시보드",
    page_icon="🔗",
    layout="wide",
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
PARENT_APP_URL = os.getenv("PARENT_APP_URL", os.getenv("APP_URL", ""))

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ 환경변수에 SUPABASE_URL과 SUPABASE_KEY를 넣어주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
<style>
html, body, [class*="css"] { font-size: 18px !important; }
[data-testid="stAppViewContainer"] { background-color: #FFF8F5; }
[data-testid="stHeader"] { background-color: #FFF8F5; }
.metric-card {
    background: white; border-radius: 16px; padding: 1.4rem;
    border-left: 6px solid #E8543A; margin-bottom: 1rem;
}
.log-card {
    background: white; border-radius: 12px; padding: 1rem 1.4rem;
    margin-bottom: 0.8rem; border: 1px solid #F0E8E4;
}
.guide-card {
    background:#FFF0EC; border-radius:12px; padding:1.2rem;
    margin-bottom:1rem; font-size:1rem; line-height:1.8;
}
.stButton > button {
    background-color: #E8543A !important; color: white !important;
    font-size: 1.05rem !important; font-weight: 700 !important;
    border-radius: 12px !important; border: none !important;
    width: 100% !important; padding: 0.7rem !important;
}
.stTextInput > div > input { font-size: 1.05rem !important; border-radius: 10px !important; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 세션
# =========================================================
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# =========================================================
# 공통 함수
# =========================================================
def safe_parse_datetime(value: str):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def get_parent_url(parent_code: str) -> str:
    if PARENT_APP_URL:
        return f"{PARENT_APP_URL}?code={parent_code}"
    return "PARENT_APP_URL 환경변수를 설정하면 부모님용 주소가 자동으로 만들어집니다."


@st.cache_data(ttl=60)
def load_logs(parent_code: str):
    try:
        result = supabase.table("usage_logs")\
            .select("*")\
            .eq("user_id", parent_code)\
            .order("created_at", desc=True)\
            .limit(200)\
            .execute()
        return result.data or []
    except Exception:
        return []


# =========================================================
# 헤더
# =========================================================
st.markdown(
    """
<h1 style='color:#E8543A; font-size:2.5rem; margin-bottom:0;'>🔗 이음이</h1>
<p style='color:#888; font-size:1.1rem;'>자녀용 케어 대시보드</p>
<hr style='border:1px solid #F0E8E4;'>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 로그인 / 회원가입
# =========================================================
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])

        with tab1:
            st.markdown("#### 자녀 계정으로 로그인하세요")
            email = st.text_input("이메일", key="login_email", placeholder="example@email.com")
            password = st.text_input("비밀번호", type="password", key="login_pw", placeholder="비밀번호 입력")

            if st.button("로그인", key="login_btn"):
                if not email or not password:
                    st.error("이메일과 비밀번호를 입력해주세요.")
                else:
                    try:
                        res = supabase.auth.sign_in_with_password({
                            "email": email,
                            "password": password,
                        })
                        st.session_state.user = res.user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    except Exception:
                        st.error("이메일 또는 비밀번호가 틀렸어요.")

        with tab2:
            st.markdown("#### 새 계정을 만드세요")
            new_email = st.text_input("이메일", key="reg_email", placeholder="example@email.com")
            new_name = st.text_input("이름", key="reg_name", placeholder="홍길동")
            new_pw = st.text_input("비밀번호", type="password", key="reg_pw", placeholder="6자 이상")
            new_pw2 = st.text_input("비밀번호 확인", type="password", key="reg_pw2", placeholder="비밀번호 재입력")

            if st.button("회원가입", key="reg_btn"):
                if not new_email or not new_name or not new_pw:
                    st.error("모든 항목을 입력해주세요.")
                elif new_pw != new_pw2:
                    st.error("비밀번호가 일치하지 않아요.")
                elif len(new_pw) < 6:
                    st.error("비밀번호는 6자 이상이어야 해요.")
                else:
                    try:
                        supabase.auth.sign_up({
                            "email": new_email,
                            "password": new_pw,
                            "options": {"data": {"name": new_name}},
                        })
                        st.success("✅ 회원가입 완료! 이메일 인증 후 로그인해주세요.")
                    except Exception as e:
                        st.error(f"회원가입 실패: {e}")


# =========================================================
# 부모님 연결
# =========================================================
def show_link_parent():
    user_id = st.session_state.user.id

    linked = supabase.table("family_links")\
        .select("*")\
        .eq("child_user_id", user_id)\
        .execute()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 👴 부모님 연결하기")
        st.markdown(
            """
<div class='guide-card'>
<b>연결 방법</b><br>
1. 부모님 휴대폰에서 <b>이음이 웹앱</b>을 엽니다.<br>
2. 상단의 <b>자녀 연결 코드</b> 탭을 누릅니다.<br>
3. 표시된 코드를 아래에 입력합니다.<br><br>
※ 이제 카카오톡 '내코드'가 아니라 웹앱의 연결 코드를 사용합니다.
</div>
""",
            unsafe_allow_html=True,
        )

        if linked.data:
            st.markdown("**연결된 부모님**")
            for link in linked.data:
                col_a, col_b = st.columns([3, 1])
                parent_code = link.get("parent_kakao_id", "")
                with col_a:
                    st.markdown(f"👴 **{link.get('parent_name', '부모님')}** — 코드: `{parent_code}`")
                with col_b:
                    if st.button("연결 해제", key=f"unlink_{link['id']}"):
                        supabase.table("family_links").delete().eq("id", link["id"]).execute()
                        st.rerun()

        st.markdown("---")
        parent_name = st.text_input("부모님 이름", placeholder="예: 어머니, 아버지")
        parent_code = st.text_input("부모님 연결 코드", placeholder="예: P-1A2B3C4D")

        if st.button("연결하기"):
            parent_code = parent_code.strip().upper()
            if not parent_name or not parent_code:
                st.error("이름과 코드를 모두 입력해주세요.")
            else:
                check = supabase.table("usage_logs")\
                    .select("user_id")\
                    .eq("user_id", parent_code)\
                    .limit(1)\
                    .execute()

                if not check.data:
                    st.error("코드를 찾을 수 없어요. 부모님 웹앱의 '자녀 연결 코드' 탭에서 코드를 먼저 확인해주세요.")
                else:
                    exists = supabase.table("family_links")\
                        .select("id")\
                        .eq("child_user_id", user_id)\
                        .eq("parent_kakao_id", parent_code)\
                        .execute()

                    if exists.data:
                        st.warning("이미 연결된 부모님이에요.")
                    else:
                        supabase.table("family_links").insert({
                            "child_user_id": user_id,
                            "parent_kakao_id": parent_code,
                            "parent_name": parent_name,
                        }).execute()
                        st.success(f"✅ {parent_name}님과 연결됐어요!")
                        st.rerun()

        if st.button("← 대시보드로 가기"):
            st.session_state.page = "dashboard"
            st.rerun()


# =========================================================
# 대시보드
# =========================================================
def show_dashboard():
    user_id = st.session_state.user.id
    user_name = st.session_state.user.user_metadata.get("name", "자녀")

    col_title, col_btn1, col_btn2 = st.columns([4, 1, 1])
    with col_title:
        st.markdown(f"**{user_name}**님의 대시보드")
    with col_btn1:
        if st.button("👴 부모님 연결"):
            st.session_state.page = "link"
            st.rerun()
    with col_btn2:
        if st.button("로그아웃"):
            st.session_state.user = None
            st.session_state.page = "login"
            supabase.auth.sign_out()
            st.rerun()

    linked = supabase.table("family_links")\
        .select("*")\
        .eq("child_user_id", user_id)\
        .execute()

    if not linked.data:
        st.markdown(
            """
<div style='text-align:center; padding:3rem; color:#aaa; font-size:1.3rem;'>
👴 아직 부모님이 연결되지 않았어요.<br>
위의 <b>부모님 연결</b> 버튼을 눌러 연결해주세요.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    parent_names = [l.get("parent_name", "부모님") for l in linked.data]
    parent_codes = [l.get("parent_kakao_id", "") for l in linked.data]

    if len(parent_names) > 1:
        selected_idx = st.radio("부모님 선택", range(len(parent_names)), format_func=lambda i: parent_names[i], horizontal=True)
    else:
        selected_idx = 0

    selected_parent_name = parent_names[selected_idx]
    selected_parent_code = parent_codes[selected_idx]

    st.markdown(f"### 👴 {selected_parent_name}님 사용 현황")
    st.text_input("부모님용 웹앱 주소", value=get_parent_url(selected_parent_code))

    logs = load_logs(selected_parent_code)
    logs_for_stats = [l for l in logs if l.get("question") != "코드발급"]

    if not logs_for_stats:
        st.markdown(
            """
<div style='text-align:center; padding:3rem; color:#aaa; font-size:1.2rem;'>
📱 아직 사용 기록이 없어요.<br>
부모님이 웹앱에 사진을 올리면 여기에 표시됩니다.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    today = datetime.now().date()
    today_logs = []
    week_logs = []
    image_logs = []

    for log in logs_for_stats:
        dt = safe_parse_datetime(log.get("created_at", ""))
        if dt:
            if dt.date() == today:
                today_logs.append(log)
            if dt.date() >= today - timedelta(days=7):
                week_logs.append(log)
        if log.get("has_image"):
            image_logs.append(log)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
<div class='metric-card'>
<p style='color:#888; font-size:1rem; margin:0;'>오늘 질문</p>
<p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(today_logs)}번</p>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
<div class='metric-card'>
<p style='color:#888; font-size:1rem; margin:0;'>이번 주 사용</p>
<p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(week_logs)}번</p>
</div>
""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
<div class='metric-card'>
<p style='color:#888; font-size:1rem; margin:0;'>사진 질문</p>
<p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(image_logs)}번</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 📋 최근 사용 기록")

    for log in logs_for_stats[:30]:
        dt = safe_parse_datetime(log.get("created_at", ""))
        time_str = dt.strftime("%m월 %d일 %H:%M") if dt else log.get("created_at", "")
        icon = "📷" if log.get("has_image") else "💬"
        question = log.get("question", "")
        answer = log.get("answer", "")
        answer_short = answer[:160] + "..." if len(answer) > 160 else answer

        st.markdown(f"""
<div class='log-card'>
<p style='color:#888; font-size:0.9rem; margin:0 0 0.3rem;'>{icon} {time_str}</p>
<p style='font-weight:600; margin:0 0 0.3rem;'>질문: {question}</p>
<p style='color:#555; margin:0;'>답변: {answer_short}</p>
</div>
""", unsafe_allow_html=True)

    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

    with st.expander("엑셀로 보기"):
        df = pd.DataFrame(logs_for_stats)
        st.dataframe(df, use_container_width=True)


# =========================================================
# 라우팅
# =========================================================
if st.session_state.user is None:
    show_login()
elif st.session_state.page == "link":
    show_link_parent()
else:
    show_dashboard()
