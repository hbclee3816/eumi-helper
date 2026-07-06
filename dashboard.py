import os
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd

load_dotenv()

st.set_page_config(
    page_title="이음이 — 자녀 대시보드",
    page_icon="🔗",
    layout="wide"
)

st.markdown("""
<style>
html, body, [class*="css"] { font-size: 18px !important; }
[data-testid="stAppViewContainer"] { background-color: #FFF8F5; }
[data-testid="stHeader"] { background-color: #FFF8F5; }
.metric-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    border-left: 6px solid #E8543A;
    margin-bottom: 1rem;
}
.log-card {
    background: white;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 0.8rem;
    border: 1px solid #F0E8E4;
}
.stButton > button {
    background-color: #E8543A !important;
    color: white !important;
    font-size: 1.1rem !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: none !important;
    width: 100% !important;
    padding: 0.7rem !important;
}
.stTextInput > div > input {
    font-size: 1.1rem !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Supabase 연결 ──────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ 환경변수에 SUPABASE_URL과 SUPABASE_KEY를 넣어주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── 세션 초기화 ────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# ─── 헤더 ───────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#E8543A; font-size:2.5rem; margin-bottom:0;'>🔗 이음이</h1>
<p style='color:#888; font-size:1.1rem;'>자녀용 케어 대시보드</p>
<hr style='border:1px solid #F0E8E4;'>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 로그인 / 회원가입 화면
# ════════════════════════════════════════════════════════════
def show_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])

        # ─── 로그인 탭 ─────────────────────────────────────
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
                            "password": password
                        })
                        st.session_state.user = res.user
                        st.session_state.page = "dashboard"
                        st.rerun()
                    except Exception as e:
                        st.error("이메일 또는 비밀번호가 틀렸어요.")

        # ─── 회원가입 탭 ───────────────────────────────────
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
                        res = supabase.auth.sign_up({
                            "email": new_email,
                            "password": new_pw,
                            "options": {"data": {"name": new_name}}
                        })
                        st.success("✅ 회원가입 완료! 이메일을 확인해주세요. 인증 후 로그인 가능해요.")
                    except Exception as e:
                        st.error(f"회원가입 실패: {str(e)}")


# ════════════════════════════════════════════════════════════
# 부모님 연결 화면
# ════════════════════════════════════════════════════════════
def show_link_parent():
    user_id = st.session_state.user.id

    # 이미 연결된 부모님 확인
    linked = supabase.table("family_links")\
        .select("*")\
        .eq("child_user_id", user_id)\
        .execute()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 👴 부모님 연결하기")
        st.markdown("""
        <div style='background:#FFF0EC; border-radius:12px; padding:1.2rem; margin-bottom:1rem; font-size:1rem; line-height:1.8;'>
        <b>연결 방법</b><br>
        1. 부모님이 카카오톡에서 이음이에게 <b>"내코드"</b> 라고 보내세요<br>
        2. 이음이가 부모님께 코드를 알려드려요<br>
        3. 그 코드를 아래에 입력하세요
        </div>
        """, unsafe_allow_html=True)

        # 이미 연결된 부모님 목록
        if linked.data:
            st.markdown("**연결된 부모님**")
            for link in linked.data:
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.markdown(f"👴 **{link['parent_name']}** — 코드: `{link['parent_kakao_id'][:8]}...`")
                with col_b:
                    if st.button("연결 해제", key=f"unlink_{link['id']}"):
                        supabase.table("family_links").delete().eq("id", link["id"]).execute()
                        st.rerun()

        st.markdown("---")
        st.markdown("**새 부모님 연결**")
        parent_name = st.text_input("부모님 이름", placeholder="예: 어머니, 아버지")
        parent_code = st.text_input("부모님 코드", placeholder="이음이가 알려준 코드 입력")

        if st.button("연결하기"):
            if not parent_name or not parent_code:
                st.error("이름과 코드를 모두 입력해주세요.")
            else:
                # 코드로 usage_logs에서 user_id 확인
                check = supabase.table("usage_logs")\
                    .select("user_id")\
                    .eq("user_id", parent_code)\
                    .limit(1)\
                    .execute()

                if not check.data:
                    st.error("코드를 찾을 수 없어요. 부모님이 이음이에게 '내코드'를 먼저 보내주세요.")
                else:
                    # 이미 연결됐는지 확인
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
                            "parent_name": parent_name
                        }).execute()
                        st.success(f"✅ {parent_name}님과 연결됐어요!")
                        st.rerun()

        if st.button("← 대시보드로 가기"):
            st.session_state.page = "dashboard"
            st.rerun()


# ════════════════════════════════════════════════════════════
# 메인 대시보드 화면
# ════════════════════════════════════════════════════════════
def show_dashboard():
    user_id = st.session_state.user.id
    user_name = st.session_state.user.user_metadata.get("name", "자녀")

    # 상단 메뉴
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

    # 연결된 부모님 목록
    linked = supabase.table("family_links")\
        .select("*")\
        .eq("child_user_id", user_id)\
        .execute()

    if not linked.data:
        st.markdown("""
        <div style='text-align:center; padding:3rem; color:#aaa; font-size:1.3rem;'>
            👴 아직 부모님이 연결되지 않았어요.<br>
            위의 <b>"부모님 연결"</b> 버튼을 눌러서 연결해주세요!
        </div>
        """, unsafe_allow_html=True)
        return

    # 부모님 선택 탭
    parent_names = [l["parent_name"] for l in linked.data]
    parent_ids = [l["parent_kakao_id"] for l in linked.data]

    if len(parent_names) > 1:
        selected_idx = st.radio("부모님 선택", range(len(parent_names)),
                                 format_func=lambda i: parent_names[i], horizontal=True)
    else:
        selected_idx = 0

    selected_parent_name = parent_names[selected_idx]
    selected_parent_id = parent_ids[selected_idx]

    st.markdown(f"### 👴 {selected_parent_name}님 사용 현황")

    # 데이터 불러오기
    @st.cache_data(ttl=60)
    def load_logs(parent_id):
        try:
            result = supabase.table("usage_logs")\
                .select("*")\
                .eq("user_id", parent_id)\
                .order("created_at", desc=True)\
                .limit(100)\
                .execute()
            return result.data
        except:
            return []

    logs = load_logs(selected_parent_id)

    if not logs:
        st.markdown("""
        <div style='text-align:center; padding:3rem; color:#aaa; font-size:1.2rem;'>
            📱 아직 사용 기록이 없어요.<br>
            부모님이 이음이에게 사진을 보내시면 여기에 표시돼요!
        </div>
        """, unsafe_allow_html=True)
        return

    # 요약 카드
    today = datetime.now().date()
    today_logs = [l for l in logs if l["created_at"][:10] == str(today)]
    week_logs = [l for l in logs if
        datetime.fromisoformat(l["created_at"]).date() >= today - timedelta(days=7)]
    image_logs = [l for l in logs if l.get("has_image")]

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

    for log in logs[:20]:
        time_str = datetime.fromisoformat(log["created_at"]).strftime("%m월 %d일 %H:%M")
        icon = "📷" if log.get("has_image") else "💬"
        question = log.get("question", "")
        answer = log.get("answer", "")
        answer_short = answer[:100] + "..." if len(answer) > 100 else answer

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

    st.markdown("""
    <p style='text-align:center; color:#ccc; font-size:0.85rem; margin-top:2rem;'>
    이음이 — 디지털과 어르신을 잇다
    </p>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# 페이지 라우팅
# ════════════════════════════════════════════════════════════
if st.session_state.user is None:
    show_login()
elif st.session_state.page == "link":
    show_link_parent()
else:
    show_dashboard()
