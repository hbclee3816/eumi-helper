import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from google import genai
from supabase import create_client

load_dotenv()

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="이음이 — 부모님용 디지털 도우미",
    page_icon="🔗",
    layout="centered",
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
AUTH_SECRET = os.getenv("AUTH_SECRET", "eumi-dev-secret-change-me")
APP_URL = os.getenv("APP_URL", "")

SUPABASE_APP_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY

if not SUPABASE_URL or not SUPABASE_APP_KEY:
    st.error("⚠️ SUPABASE_URL과 SUPABASE_KEY를 Streamlit Secrets에 넣어주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_APP_KEY)

# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
<style>
html, body, [class*="css"] { font-size: 24px !important; }
[data-testid="stAppViewContainer"] { background-color: #FFF8F5; }
[data-testid="stHeader"] { background-color: #FFF8F5; }
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], p, li, label, div { line-height: 1.7; }
.title-area { text-align: center; padding: 1.6rem 0 1rem 0; }
.title-main { font-size: 4.6rem; font-weight: 900; color: #E8543A; line-height: 1.1; }
.title-sub { font-size: 2rem; color: #666; margin-top: 0.8rem; line-height: 1.7; }
.guide-card {
    background: #FFF0EC; border-radius: 18px; padding: 1.7rem 1.8rem;
    font-size: 1.55rem; color: #333; margin: 1rem 0 1.2rem 0; line-height: 1.95;
}
.code-card {
    background: #ffffff; border: 3px solid #F0C4B8; border-radius: 22px;
    padding: 1.6rem 1.6rem; margin: 1.1rem 0; text-align: center;
}
.code-big { font-size: 2.9rem; font-weight: 900; color: #E8543A; letter-spacing: 0.08em; }
.answer-card {
    background: #ffffff; border-left: 10px solid #E8543A; border-radius: 0 22px 22px 0;
    padding: 1.9rem 2.1rem; font-size: 1.7rem; line-height: 2.0; color: #222;
    margin-top: 1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.folder-card {
    background:#fff; border:2px solid #F0D8D0; border-radius:16px; padding:1.2rem 1.4rem;
    margin:0.9rem 0; font-size:1.4rem; line-height:1.9;
}
.small-note { color:#666; font-size:1.15rem; line-height:1.8; }
[data-testid="stFileUploader"] {
    background: #fff; border-radius: 18px; padding: 1.5rem; border: 3px dashed #F0C4B8;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small { font-size: 1.35rem !important; }
.stButton > button {
    background-color: #E8543A !important; color: white !important;
    font-size: 1.55rem !important; font-weight: 800 !important;
    padding: 1rem 1.5rem !important; border-radius: 18px !important;
    border: none !important; width: 100% !important; min-height: 4.2rem !important;
}
.stButton > button:hover { background-color: #C9422A !important; }
.stTextInput > div > input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    font-size: 1.35rem !important; border-radius: 14px !important; min-height: 3.4rem !important;
}
label, .stTextInput label, .stTextArea label, .stSelectbox label { font-size: 1.35rem !important; font-weight: 700 !important; }
button[data-baseweb="tab"] { font-size: 1.35rem !important; font-weight: 800 !important; padding-top: 0.6rem !important; padding-bottom: 0.8rem !important; }
[data-testid="stAlertContainer"] p, [data-testid="stAlertContainer"] div { font-size: 1.3rem !important; }
h1 { font-size: 3rem !important; }
h2, h3 { font-size: 2rem !important; }
hr { border: none; border-top: 2px solid #F0E8E4; margin: 1.7rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 세션
# =========================================================
if "parent_user" not in st.session_state:
    st.session_state.parent_user = None
if "last_classification" not in st.session_state:
    st.session_state.last_classification = None

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
    digits = digits_only(value)
    return digits


def hash_password(phone_digits: str, password: str) -> str:
    raw = f"{AUTH_SECRET}:{phone_digits}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def make_parent_code() -> str:
    return "P-" + uuid.uuid4().hex[:8].upper()


def create_user(role: str, phone_digits: str, name: str, password: str) -> Dict[str, Any]:
    existing = supabase.table("eumi_users")\
        .select("id")\
        .eq("role", role)\
        .eq("phone", phone_digits)\
        .limit(1)\
        .execute()
    if existing.data:
        raise ValueError("이미 가입된 휴대폰 번호입니다. 로그인해주세요.")

    data = {
        "role": role,
        "phone": phone_digits,
        "name": name.strip(),
        "password_hash": hash_password(phone_digits, password),
    }
    if role == "parent":
        data["parent_code"] = make_parent_code()

    res = supabase.table("eumi_users").insert(data).execute()
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
    if APP_URL:
        return f"{APP_URL}?code={parent_code}"
    return f"부모님용 앱 주소 뒤에 ?code={parent_code} 를 붙여서 저장하세요."


def safe_json_loads(text: str) -> Dict[str, Any]:
    if not text:
        return {}
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        cleaned = match.group(0)
    try:
        return json.loads(cleaned)
    except Exception:
        return {}


def normalize_folder_value(value: str, default: str) -> str:
    value = (value or "").strip()
    value = re.sub(r"[\n\r\t]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value[:30] if value else default


def build_folder_key(category: str, place_name: str) -> str:
    category = normalize_folder_value(category, "기타")
    place_name = normalize_folder_value(place_name, "미분류")
    return f"{category}__{place_name}"


def classify_image(image: Image.Image, question: str) -> Dict[str, str]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image.convert("RGB").save(tmp.name, format="JPEG")
            tmp_path = tmp.name
        uploaded_image = client.files.upload(file=tmp_path)

        prompt = f"""
다음 이미지는 어르신이 디지털 사용 중 어려워서 올린 화면입니다.
질문: {question}

아래 JSON 형식으로만 답하세요.
- category: 큰 분류. 예: 키오스크, 병원 앱, 은행 앱, 기차/교통, 배달/쇼핑, 주민센터/공공, 기타
- place_name: 장소명/브랜드명/앱명. 예: 맥도날드, 버거킹, 병원 무인접수기, 코레일, 국민은행. 모르면 미분류
- task_name: 하려는 일. 예: 주문하기, 결제하기, 접수하기, 예매하기, 로그인하기
- short_title: 나중에 기록에서 볼 짧은 제목

{{"category":"", "place_name":"", "task_name":"", "short_title":""}}
""".strip()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, uploaded_image],
            config={"response_mime_type": "application/json"},
        )
        data = safe_json_loads(response.text or "")
        category = normalize_folder_value(str(data.get("category", "")), "기타")
        place_name = normalize_folder_value(str(data.get("place_name", "")), "미분류")
        task_name = normalize_folder_value(str(data.get("task_name", "")), "도움 요청")
        short_title = normalize_folder_value(str(data.get("short_title", "")), task_name)
        return {
            "category": category,
            "place_name": place_name,
            "task_name": task_name,
            "short_title": short_title,
            "folder_key": build_folder_key(category, place_name),
        }
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def load_previous_logs(parent_user_id: str, folder_key: str, limit: int = 5) -> List[Dict[str, Any]]:
    try:
        res = supabase.table("usage_logs")\
            .select("id, question, answer, task_name, short_title, created_at")\
            .eq("parent_user_id", parent_user_id)\
            .eq("folder_key", folder_key)\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()
        return res.data or []
    except Exception:
        return []


def make_previous_context(logs: List[Dict[str, Any]]) -> str:
    if not logs:
        return "이 장소/분류의 이전 질문 기록은 없습니다."
    lines = []
    for idx, log in enumerate(logs, start=1):
        q = (log.get("question") or "")[:120]
        a = (log.get("answer") or "")[:220]
        title = log.get("short_title") or log.get("task_name") or "이전 질문"
        created = (log.get("created_at") or "")[:10]
        lines.append(f"{idx}. [{created}] {title}\n질문: {q}\n이전 답변 요약: {a}")
    return "\n\n".join(lines)


def answer_image(image: Image.Image, question: str, classification: Dict[str, str], previous_logs: List[Dict[str, Any]]) -> str:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image.convert("RGB").save(tmp.name, format="JPEG")
            tmp_path = tmp.name
        uploaded_image = client.files.upload(file=tmp_path)

        system_instruction = (
            "당신은 디지털 기기가 익숙하지 않은 어르신을 돕는 친절한 안내자입니다. "
            "어려운 용어 대신 쉬운 말로 설명하세요. 화면의 위치, 색깔, 버튼 모양을 구체적으로 말하세요. "
            "한 번에 너무 많은 단계를 말하지 말고, 지금 바로 누를 곳을 먼저 알려주세요. "
            "개인정보, 결제, 송금, 비밀번호 입력 화면에서는 무리하게 진행시키지 말고 자녀나 직원에게 확인하라고 안내하세요."
        )

        prompt = f"""
사용자가 올린 화면 분류:
- 큰 분류: {classification.get('category')}
- 장소/앱/브랜드: {classification.get('place_name')}
- 하려는 일: {classification.get('task_name')}

이번 질문:
{question}

같은 폴더의 이전 질문 기록:
{make_previous_context(previous_logs)}

답변 규칙:
1. 이전에 비슷한 질문이 있으면 "전에 비슷한 질문을 하셨어요"라고 먼저 알려주세요.
2. 이번 화면에서 바로 해야 할 행동을 1~3단계로 안내하세요.
3. 버튼 위치, 색상, 글자를 구체적으로 말하세요.
4. 위험한 결제/송금/개인정보 화면이면 자녀나 직원에게 확인하라고 말하세요.
""".strip()

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, uploaded_image],
            config={"system_instruction": system_instruction},
        )
        return response.text or "답변을 만들지 못했어요. 사진을 조금 더 선명하게 다시 올려주세요."
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def save_log(parent_user: Dict[str, Any], question: str, answer: str, classification: Dict[str, str], has_image: bool, image_name: str = "") -> None:
    supabase.table("usage_logs").insert({
        "user_id": parent_user.get("parent_code"),
        "parent_user_id": parent_user.get("id"),
        "parent_code": parent_user.get("parent_code"),
        "category": classification.get("category", "기타"),
        "place_name": classification.get("place_name", "미분류"),
        "task_name": classification.get("task_name", "도움 요청"),
        "folder_key": classification.get("folder_key", "기타__미분류"),
        "short_title": classification.get("short_title", "질문"),
        "question": question,
        "answer": answer,
        "has_image": has_image,
        "image_name": image_name,
        "created_at": datetime.now().isoformat(),
    }).execute()


def load_my_logs(parent_user_id: str) -> List[Dict[str, Any]]:
    try:
        res = supabase.table("usage_logs")\
            .select("*")\
            .eq("parent_user_id", parent_user_id)\
            .order("created_at", desc=True)\
            .limit(500)\
            .execute()
        return res.data or []
    except Exception as e:
        st.error(f"기록을 불러오지 못했습니다: {e}")
        return []


def logout() -> None:
    st.session_state.parent_user = None
    st.rerun()

# =========================================================
# 로그인 화면
# =========================================================
def show_auth() -> None:
    st.markdown(
        """
<div class="title-area">
    <div class="title-main">🔗 이음이</div>
    <div class="title-sub">부모님용 디지털 도우미<br>기록이 남아서 나중에 다시 볼 수 있어요</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([0.35, 4.3, 0.35])
    with col2:
        tab_login, tab_join = st.tabs(["🔐 로그인", "📝 처음 사용"])

        with tab_login:
            st.markdown("### 부모님 계정으로 로그인")
            phone = phone_input("휴대폰 번호", "parent_login_phone")
            pw = st.text_input("비밀번호", type="password", key="parent_login_pw", placeholder="비밀번호 입력")
            submitted = st.button("로그인", key="parent_login_submit")
            if submitted:
                if len(phone) != 11:
                    st.error("휴대폰 번호 11자리를 입력해주세요.")
                elif not pw:
                    st.error("비밀번호를 입력해주세요.")
                else:
                    try:
                        st.session_state.parent_user = login_user("parent", phone, pw)
                        st.success("로그인되었습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

        with tab_join:
            st.markdown("### 처음 사용하는 분")
            phone = phone_input("휴대폰 번호", "parent_join_phone")
            name = st.text_input("이름", key="parent_join_name", placeholder="예: 홍길동")
            pw = st.text_input("비밀번호", type="password", key="parent_join_pw", placeholder="6자 이상")
            pw2 = st.text_input("비밀번호 확인", type="password", key="parent_join_pw2", placeholder="비밀번호 다시 입력")
            submitted = st.button("계정 만들기", key="parent_join_submit")
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
                        user = create_user("parent", phone, name, pw)
                        st.session_state.parent_user = user
                        st.success("계정이 만들어졌습니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"회원가입 실패: {e}")

# =========================================================
# 메인 화면
# =========================================================
def show_main() -> None:
    parent_user = st.session_state.parent_user
    parent_code = parent_user.get("parent_code")

    st.markdown(
        f"""
<div class="title-area">
    <div class="title-main">🔗 이음이</div>
    <div class="title-sub">{parent_user.get('name', '부모님')}님, 막히는 화면을 사진으로 올려주세요</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(f"<div class='small-note'><b>내 연결 코드:</b> {parent_code}</div>", unsafe_allow_html=True)
    with col_b:
        if st.button("로그아웃"):
            logout()

    tab_help, tab_history, tab_code = st.tabs(["📷 사진으로 물어보기", "📁 내 기록", "👨‍👩‍👧 자녀 연결 코드"])

    with tab_help:
        st.markdown("#### 📷 막히는 화면 사진을 올려주세요")
        st.markdown(
            """
<div class="guide-card">
키오스크, 병원 앱, 은행 앱, 기차 예매 화면처럼<br>
<b>어디를 눌러야 할지 모를 때 화면을 찍어서 올려주세요.</b><br>
이음이가 장소별로 기록을 정리해두고, 다음에 비슷한 화면을 물어보면 이전 기록도 함께 참고합니다.
</div>
""",
            unsafe_allow_html=True,
        )

        uploaded_file = st.file_uploader("사진 선택", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="올린 화면", use_container_width=True)

            question = st.text_input(
                "궁금한 점",
                value="이 화면에서 다음에 뭘 누르면 되나요?",
                help="그냥 두셔도 됩니다.",
            )

            if st.button("✨ AI에게 물어보기"):
                with st.spinner("AI가 화면을 분류하고 이전 기록을 찾고 있어요 🙏"):
                    try:
                        classification = classify_image(image, question)
                        previous_logs = load_previous_logs(parent_user.get("id"), classification["folder_key"])
                        answer = answer_image(image, question, classification, previous_logs)
                        save_log(parent_user, question, answer, classification, has_image=True, image_name=uploaded_file.name)

                        st.success("기록이 저장되었습니다.")
                        st.markdown("#### 📂 자동 분류")
                        st.markdown(
                            f"""
<div class="folder-card">
<b>큰 분류:</b> {classification['category']}<br>
<b>장소/앱:</b> {classification['place_name']}<br>
<b>하려는 일:</b> {classification['task_name']}
</div>
""",
                            unsafe_allow_html=True,
                        )

                        if previous_logs:
                            with st.expander("전에 비슷하게 물어본 기록 보기"):
                                for log in previous_logs:
                                    st.markdown(f"**{(log.get('created_at') or '')[:10]} — {log.get('short_title') or log.get('task_name')}**")
                                    st.write(log.get("question", ""))
                                    st.caption((log.get("answer") or "")[:250] + "...")

                        st.markdown("#### 📣 AI 답변")
                        st.markdown(f'<div class="answer-card">{answer}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"오류가 발생했어요: {e}")
        else:
            st.markdown(
                """
<div class="guide-card" style="text-align:center; padding: 2rem;">
📱 위의 버튼을 눌러 화면 사진을 올리면<br>
AI가 <b>다음에 뭘 눌러야 하는지</b> 바로 알려드려요.
</div>
""",
                unsafe_allow_html=True,
            )

    with tab_history:
        st.markdown("#### 📁 내가 물어본 기록")
        logs = load_my_logs(parent_user.get("id"))
        if not logs:
            st.info("아직 저장된 질문 기록이 없습니다.")
        else:
            folders: Dict[str, List[Dict[str, Any]]] = {}
            for log in logs:
                key = log.get("folder_key") or build_folder_key(log.get("category", "기타"), log.get("place_name", "미분류"))
                folders.setdefault(key, []).append(log)

            folder_options = []
            for key, items in sorted(folders.items(), key=lambda x: len(x[1]), reverse=True):
                sample = items[0]
                label = f"📁 {sample.get('category', '기타')} > {sample.get('place_name', '미분류')} ({len(items)}회)"
                folder_options.append((label, key))

            selected_label = st.selectbox("폴더 선택", [x[0] for x in folder_options])
            selected_key = dict(folder_options)[selected_label]
            selected_logs = folders[selected_key]

            st.markdown(f"### {selected_label}")
            for log in selected_logs:
                title = log.get("short_title") or log.get("task_name") or "질문"
                created = (log.get("created_at") or "")[:16].replace("T", " ")
                with st.expander(f"{created} · {title}"):
                    st.markdown(f"**질문**: {log.get('question', '')}")
                    st.markdown("**답변**")
                    st.write(log.get("answer", ""))

    with tab_code:
        st.markdown("#### 👨‍👩‍👧 자녀에게 알려줄 코드")
        st.markdown(
            f"""
<div class="code-card">
    <div class="small-note">자녀 대시보드에서 아래 코드를 입력하면 사용 기록을 볼 수 있습니다.</div>
    <div class="code-big">{parent_code}</div>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown("#### 부모님 휴대폰에 저장할 주소")
        st.info(get_parent_url(parent_code))
        st.markdown(
            """
<div class="guide-card">
<b>부모님 휴대폰에 저장하는 방법</b><br>
1. 위 주소를 부모님 휴대폰에서 엽니다.<br>
2. 브라우저 메뉴에서 <b>홈 화면에 추가</b>를 누릅니다.<br>
3. 다음부터는 홈 화면의 이음이 아이콘만 누르면 됩니다.
</div>
""",
            unsafe_allow_html=True,
        )

if st.session_state.parent_user is None:
    show_auth()
else:
    show_main()
