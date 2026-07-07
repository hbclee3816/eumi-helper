import hashlib
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

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
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
AUTH_SECRET = os.getenv("AUTH_SECRET", "eumi-dev-secret-change-me")
PARENT_APP_URL = os.getenv("PARENT_APP_URL", os.getenv("APP_URL", ""))

SUPABASE_APP_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
if not SUPABASE_URL or not SUPABASE_APP_KEY:
    st.error("⚠️ SUPABASE_URL과 SUPABASE_SERVICE_ROLE_KEY를 Streamlit Secrets에 넣어주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_APP_KEY)

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
.folder-card {
    background:#fff; border:1px solid #F0D8D0; border-radius:14px; padding:1rem 1.2rem;
    margin:0.7rem 0; line-height:1.7;
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
if "child_user" not in st.session_state:
    st.session_state.child_user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# =========================================================
# 공통 함수
# =========================================================
def digits_only(value: str) -> str:
    return re.sub(r"\D", "", value or "")[:11]


def format_phone(digits: str) -> str:
    digits = digits_only(digits)
    if len(digits) <= 3:
        return digits
    if len(digits) <= 7:
        return f"{digits[:3]}-{digits[3:]}"
    return f"{digits[:3]}-{digits[3:7]}-{digits[7:11]}"


def normalize_phone_input(key: str) -> None:
    raw = st.session_state.get(key, "")
    formatted = format_phone(raw)
    if raw != formatted:
        st.session_state[key] = formatted


def phone_input(label: str, key: str) -> str:
    value = st.text_input(
        label,
        key=key,
        placeholder="010-0000-0000",
        help="숫자 11자리까지만 입력하세요. - 는 자동으로 정리됩니다.",
        on_change=normalize_phone_input,
        args=(key,),
    )
    return digits_only(value)


def hash_password(phone_digits: str, password: str) -> str:
    raw = f"{AUTH_SECRET}:{phone_digits}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def create_user(role: str, phone_digits: str, name: str, password: str) -> Dict[str, Any]:
    existing = supabase.table("eumi_users")\
        .select("id")\
        .eq("role", role)\
        .eq("phone", phone_digits)\
        .limit(1)\
        .execute()
    if existing.data:
        raise ValueError("이미 가입된 휴대폰 번호입니다. 로그인해주세요.")

    res = supabase.table("eumi_users").insert({
        "role": role,
        "phone": phone_digits,
        "name": name.strip(),
        "password_hash": hash_password(phone_digits, password),
    }).execute()
    if not res.data:
        raise RuntimeError("계정을 만들지 못했습니다.")
    return res.data[0]


def login_user(role: str, phone_digits: str, password: str) -> Dict[str, Any]:
    res = supabase.table("eumi_users")\
        .select("*")\
        .eq("role", role)\
        .eq("phone", phone_digits)\
        .limit(1)\
        .execute()
    if not res.data:
        raise ValueError("가입되지 않은 휴대폰 번호입니다.")
    user = res.data[0]
    if user.get("password_hash") != hash_password(phone_digits, password):
        raise ValueError("비밀번호가 틀렸습니다.")
    return user


def get_parent_url(parent_code: str) -> str:
    if PARENT_APP_URL:
        return f"{PARENT_APP_URL}?code={parent_code}"
    return "PARENT_APP_URL 환경변수를 설정하면 부모님용 주소가 자동으로 만들어집니다."


def safe_parse_datetime(value: str):
    try:
        return datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    except Exception:
        return None


def load_links(child_user_id: str) -> List[Dict[str, Any]]:
    try:
        res = supabase.table("family_links")\
            .select("*")\
            .eq("child_user_id", child_user_id)\
            .order("created_at", desc=True)\
            .execute()
        return res.data or []
    except Exception as e:
        st.error(f"부모님 연결 정보를 불러오지 못했습니다: {e}")
        return []


def load_logs(parent_user_id: str, parent_code: str) -> List[Dict[str, Any]]:
    try:
        query = supabase.table("usage_logs")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(500)
        if parent_user_id:
            query = query.eq("parent_user_id", parent_user_id)
        else:
            query = query.eq("parent_code", parent_code)
        res = query.execute()
        return res.data or []
    except Exception as e:
        st.error(f"사용 기록을 불러오지 못했습니다: {e}")
        return []


def find_parent_by_code(parent_code: str) -> Dict[str, Any]:
    res = supabase.table("eumi_users")\
        .select("id, name, phone, parent_code")\
        .eq("role", "parent")\
        .eq("parent_code", parent_code)\
        .limit(1)\
        .execute()
    if not res.data:
        return {}
    return res.data[0]


def logout() -> None:
    st.session_state.child_user = None
    st.session_state.page = "login"
    st.rerun()

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
def show_login() -> None:
    if SUPABASE_SERVICE_ROLE_KEY == "":
        st.warning("⚠️ 이번 버전은 SUPABASE_SERVICE_ROLE_KEY 사용을 권장합니다. Streamlit Secrets에 추가해주세요.")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["🔐 로그인", "📝 회원가입"])

        with tab1:
            st.markdown("#### 자녀 계정으로 로그인하세요")
            phone = phone_input("휴대폰 번호", "child_login_phone")
            password = st.text_input("비밀번호", type="password", key="child_login_pw", placeholder="비밀번호 입력")
            submitted = st.button("로그인", key="child_login_submit")
            if submitted:
                if len(phone) != 11:
                    st.error("휴대폰 번호 11자리를 입력해주세요.")
                elif not password:
                    st.error("비밀번호를 입력해주세요.")
                else:
                    try:
                        st.session_state.child_user = login_user("child", phone, password)
                        st.session_state.page = "dashboard"
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        with tab2:
            st.markdown("#### 새 계정을 만드세요")
            phone = phone_input("휴대폰 번호", "child_join_phone")
            name = st.text_input("이름", key="child_join_name", placeholder="홍길동")
            pw = st.text_input("비밀번호", type="password", key="child_join_pw", placeholder="6자 이상")
            pw2 = st.text_input("비밀번호 확인", type="password", key="child_join_pw2", placeholder="비밀번호 재입력")
            submitted = st.button("회원가입", key="child_join_submit")
            if submitted:
                if len(phone) != 11:
                    st.error("휴대폰 번호 11자리를 입력해주세요.")
                elif not name.strip():
                    st.error("이름을 입력해주세요.")
                elif len(pw) < 6:
                    st.error("비밀번호는 6자 이상이어야 해요.")
                elif pw != pw2:
                    st.error("비밀번호가 일치하지 않아요.")
                else:
                    try:
                        st.session_state.child_user = create_user("child", phone, name, pw)
                        st.session_state.page = "dashboard"
                        st.success("회원가입이 완료되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"회원가입 실패: {e}")

# =========================================================
# 부모님 연결
# =========================================================
def show_link_parent() -> None:
    child_user = st.session_state.child_user
    child_user_id = child_user.get("id")

    linked = load_links(child_user_id)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("#### 👴 부모님 연결하기")
        st.markdown(
            """
<div class='guide-card'>
<b>연결 방법</b><br>
1. 부모님 휴대폰에서 <b>부모님용 이음이 앱</b>을 엽니다.<br>
2. 부모님이 로그인한 뒤 <b>자녀 연결 코드</b> 탭을 누릅니다.<br>
3. 표시된 코드를 아래에 입력합니다.<br>
4. 한 번 연결하면 부모님 기록을 계속 볼 수 있습니다.
</div>
""",
            unsafe_allow_html=True,
        )

        if linked:
            st.markdown("**연결된 부모님**")
            for link in linked:
                col_a, col_b = st.columns([3, 1])
                parent_code = link.get("parent_code", "")
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
                parent = find_parent_by_code(parent_code)
                if not parent:
                    st.error("코드를 찾을 수 없어요. 부모님 앱의 '자녀 연결 코드' 탭에서 코드를 다시 확인해주세요.")
                else:
                    exists = supabase.table("family_links")\
                        .select("id")\
                        .eq("child_user_id", child_user_id)\
                        .eq("parent_code", parent_code)\
                        .execute()
                    if exists.data:
                        st.warning("이미 연결된 부모님이에요.")
                    else:
                        supabase.table("family_links").insert({
                            "child_user_id": child_user_id,
                            "parent_user_id": parent.get("id"),
                            "parent_code": parent_code,
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
def show_dashboard() -> None:
    child_user = st.session_state.child_user
    user_name = child_user.get("name", "자녀")

    col_title, col_btn1, col_btn2 = st.columns([4, 1, 1])
    with col_title:
        st.markdown(f"**{user_name}**님의 대시보드")
    with col_btn1:
        if st.button("👴 부모님 연결"):
            st.session_state.page = "link"
            st.rerun()
    with col_btn2:
        if st.button("로그아웃"):
            logout()

    linked = load_links(child_user.get("id"))
    if not linked:
        st.markdown(
            """
<div style='text-align:center; padding:3rem; color:#aaa; font-size:1.3rem;'>
    👴 아직 부모님이 연결되지 않았어요.<br>
    위의 <b>부모님 연결</b> 버튼을 눌러서 연결해주세요.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    parent_names = [l.get("parent_name", "부모님") for l in linked]
    if len(parent_names) > 1:
        selected_idx = st.radio("부모님 선택", range(len(parent_names)), format_func=lambda i: parent_names[i], horizontal=True)
    else:
        selected_idx = 0

    selected = linked[selected_idx]
    parent_name = selected.get("parent_name", "부모님")
    parent_code = selected.get("parent_code", "")
    parent_user_id = selected.get("parent_user_id", "")

    st.markdown(f"### 👴 {parent_name}님 사용 현황")
    st.caption(f"부모님 앱 주소: {get_parent_url(parent_code)}")

    logs = load_logs(parent_user_id, parent_code)
    if not logs:
        st.markdown(
            """
<div style='text-align:center; padding:3rem; color:#aaa; font-size:1.2rem;'>
    📱 아직 사용 기록이 없어요.<br>
    부모님이 이음이에서 사진을 올리면 여기에 표시됩니다.
</div>
""",
            unsafe_allow_html=True,
        )
        return

    today = datetime.now().date()
    today_logs = []
    week_logs = []
    for log in logs:
        dt = safe_parse_datetime(log.get("created_at", ""))
        if not dt:
            continue
        if dt.date() == today:
            today_logs.append(log)
        if dt.date() >= today - timedelta(days=7):
            week_logs.append(log)

    image_logs = [l for l in logs if l.get("has_image")]
    folders: Dict[str, List[Dict[str, Any]]] = {}
    for log in logs:
        key = log.get("folder_key") or f"{log.get('category', '기타')}__{log.get('place_name', '미분류')}"
        folders.setdefault(key, []).append(log)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class='metric-card'><p style='color:#888; margin:0;'>오늘 질문</p>
        <p style='color:#E8543A; font-size:2.3rem; font-weight:700; margin:0;'>{len(today_logs)}번</p></div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class='metric-card'><p style='color:#888; margin:0;'>이번 주 사용</p>
        <p style='color:#E8543A; font-size:2.3rem; font-weight:700; margin:0;'>{len(week_logs)}번</p></div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class='metric-card'><p style='color:#888; margin:0;'>사진 질문</p>
        <p style='color:#E8543A; font-size:2.3rem; font-weight:700; margin:0;'>{len(image_logs)}번</p></div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class='metric-card'><p style='color:#888; margin:0;'>기록 폴더</p>
        <p style='color:#E8543A; font-size:2.3rem; font-weight:700; margin:0;'>{len(folders)}개</p></div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    tab_summary, tab_folder, tab_recent = st.tabs(["📊 자주 어려워한 곳", "📁 장소별 기록", "📋 최근 기록"])

    with tab_summary:
        st.markdown("#### 부모님이 자주 어려워한 화면")
        folder_rows = []
        for key, items in folders.items():
            sample = items[0]
            folder_rows.append({
                "분류": sample.get("category", "기타"),
                "장소/앱": sample.get("place_name", "미분류"),
                "질문 횟수": len(items),
                "최근 질문": (items[0].get("created_at") or "")[:10],
            })
        df = pd.DataFrame(folder_rows).sort_values("질문 횟수", ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

        top = folder_rows[0] if folder_rows else None
        if top:
            st.info(f"가장 많이 어려워한 곳은 **{top['분류']} > {top['장소/앱']}** 입니다.")

    with tab_folder:
        folder_options = []
        for key, items in sorted(folders.items(), key=lambda x: len(x[1]), reverse=True):
            sample = items[0]
            label = f"📁 {sample.get('category', '기타')} > {sample.get('place_name', '미분류')} ({len(items)}회)"
            folder_options.append((label, key))

        selected_label = st.selectbox("폴더 선택", [x[0] for x in folder_options])
        selected_key = dict(folder_options)[selected_label]
        selected_logs = folders[selected_key]

        for log in selected_logs:
            title = log.get("short_title") or log.get("task_name") or "질문"
            created = (log.get("created_at") or "")[:16].replace("T", " ")
            with st.expander(f"{created} · {title}"):
                st.markdown(f"**하려던 일**: {log.get('task_name', '')}")
                st.markdown(f"**질문**: {log.get('question', '')}")
                st.markdown("**AI 답변**")
                st.write(log.get("answer", ""))

    with tab_recent:
        st.markdown("#### 최근 사용 기록")
        for log in logs[:30]:
            time_str = (log.get("created_at") or "")[:16].replace("T", " ")
            icon = "📷" if log.get("has_image") else "💬"
            category = log.get("category", "기타")
            place = log.get("place_name", "미분류")
            title = log.get("short_title") or log.get("task_name") or "질문"
            answer = log.get("answer", "")
            answer_short = answer[:130] + "..." if len(answer) > 130 else answer
            st.markdown(
                f"""
<div class='log-card'>
    <p style='color:#888; font-size:0.9rem; margin:0 0 0.3rem;'>{icon} {time_str} · {category} &gt; {place}</p>
    <p style='font-weight:700; margin:0 0 0.3rem;'>{title}</p>
    <p style='margin:0 0 0.3rem;'>질문: {log.get('question', '')}</p>
    <p style='color:#555; margin:0;'>답변: {answer_short}</p>
</div>
""",
                unsafe_allow_html=True,
            )

# =========================================================
# 라우팅
# =========================================================
if st.session_state.child_user is None:
    show_login()
elif st.session_state.page == "link":
    show_link_parent()
else:
    show_dashboard()
