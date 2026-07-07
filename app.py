import os
import uuid
import tempfile
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from dotenv import load_dotenv
from google import genai
from supabase import create_client

load_dotenv()

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(
    page_title="이음이 — 디지털 도우미",
    page_icon="🔗",
    layout="centered"
)



# =========================================================
# Streamlit 단축키 오작동 방지
# =========================================================
def disable_streamlit_clear_cache_shortcut() -> None:
    """Ctrl+C 복사 시 Streamlit의 Clear caches 창이 뜨지 않도록 막습니다."""
    components.html(
        """
<script>
(function () {
  const parentWindow = window.parent;
  const doc = parentWindow.document;

  if (parentWindow.__eumiClearCacheGuardInstalled) return;
  parentWindow.__eumiClearCacheGuardInstalled = true;

  function closeClearCacheDialog() {
    const dialogs = Array.from(doc.querySelectorAll('[role="dialog"], [aria-modal="true"]'));
    dialogs.forEach(function (dialog) {
      const text = dialog.innerText || '';
      if (text.indexOf('Clear caches') === -1) return;

      const buttons = Array.from(dialog.querySelectorAll('button'));
      const cancelButton = buttons.find(function (btn) {
        return (btn.innerText || '').trim().toLowerCase() === 'cancel';
      });

      if (cancelButton) {
        cancelButton.click();
        return;
      }

      const closeButton = buttons.find(function (btn) {
        return (btn.getAttribute('aria-label') || '').toLowerCase().includes('close') ||
               (btn.innerText || '').trim() === '×' ||
               (btn.innerText || '').trim().toLowerCase() === 'x';
      });
      if (closeButton) closeButton.click();
    });
  }

  doc.addEventListener('keydown', function (event) {
    const key = (event.key || '').toLowerCase();
    if ((event.ctrlKey || event.metaKey) && key === 'c') {
      // 복사 기본 기능은 그대로 두고, Streamlit 단축키 처리만 막습니다.
      event.stopPropagation();
      if (event.stopImmediatePropagation) event.stopImmediatePropagation();
      setTimeout(closeClearCacheDialog, 0);
      setTimeout(closeClearCacheDialog, 80);
    }
  }, true);

  closeClearCacheDialog();
  const observer = new MutationObserver(closeClearCacheDialog);
  observer.observe(doc.body, { childList: true, subtree: true });
})();
</script>
        """,
        height=0,
        width=0,
    )

disable_streamlit_clear_cache_shortcut()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
APP_URL = os.getenv("APP_URL", "")  # 예: https://eumi-helper.streamlit.app

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

# =========================================================
# 디자인
# =========================================================
st.markdown(
    """
<style>
html, body, [class*="css"] { font-size: 20px !important; }
[data-testid="stAppViewContainer"] { background-color: #FFF8F5; }
[data-testid="stHeader"] { background-color: #FFF8F5; }
.title-area { text-align: center; padding: 1.8rem 0 1rem 0; }
.title-main { font-size: 4rem; font-weight: 900; color: #E8543A; line-height: 1.1; }
.title-sub { font-size: 1.35rem; color: #777; margin-top: 0.6rem; line-height: 1.7; }
.guide-card {
    background: #FFF0EC; border-radius: 16px; padding: 1.4rem 1.6rem;
    font-size: 1.25rem; color: #444; margin: 0.8rem 0 1.1rem 0; line-height: 1.9;
}
.code-card {
    background: #ffffff; border: 3px solid #F0C4B8; border-radius: 18px;
    padding: 1.3rem 1.5rem; margin: 1rem 0; text-align: center;
}
.code-big { font-size: 2.3rem; font-weight: 900; color: #E8543A; letter-spacing: 0.08em; }
.answer-card {
    background: #ffffff; border-left: 8px solid #E8543A; border-radius: 0 20px 20px 0;
    padding: 1.8rem 2rem; font-size: 1.55rem; line-height: 2.1; color: #222;
    margin-top: 1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.small-note { color:#888; font-size:0.95rem; line-height:1.7; }
[data-testid="stFileUploader"] {
    background: #fff; border-radius: 16px; padding: 1.4rem; border: 3px dashed #F0C4B8;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small { font-size: 1.15rem !important; }
.stButton > button {
    background-color: #E8543A !important; color: white !important;
    font-size: 1.45rem !important; font-weight: 800 !important;
    padding: 0.9rem 1.6rem !important; border-radius: 16px !important;
    border: none !important; width: 100% !important; min-height: 4rem !important;
}
.stButton > button:hover { background-color: #C9422A !important; }
.stTextInput > div > input, .stTextArea textarea {
    font-size: 1.2rem !important; border-radius: 12px !important;
}
hr { border: none; border-top: 2px solid #F0E8E4; margin: 1.6rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# 공통 함수
# =========================================================
def get_or_create_parent_code() -> str:
    """URL의 ?code= 값을 우선 사용하고, 없으면 새 코드를 만들어 URL에 넣습니다."""
    code = st.query_params.get("code", "")
    if isinstance(code, list):
        code = code[0] if code else ""

    if not code:
        code = "P-" + uuid.uuid4().hex[:8].upper()
        st.query_params["code"] = code

    return code.strip()


def get_parent_url(parent_code: str) -> str:
    if APP_URL:
        return f"{APP_URL}?code={parent_code}"
    return f"현재 주소 뒤에 ?code={parent_code} 가 붙은 주소를 부모님 휴대폰에 저장하세요."


def save_log(parent_code: str, question: str, answer: str, has_image: bool) -> None:
    if not supabase:
        return
    try:
        supabase.table("usage_logs").insert({
            "user_id": parent_code,
            "question": question,
            "answer": answer,
            "has_image": has_image,
            "created_at": datetime.now().isoformat(),
        }).execute()
    except Exception as e:
        st.warning(f"사용 기록 저장은 실패했지만, AI 답변은 정상 표시됩니다. 오류: {e}")


def register_code_once(parent_code: str) -> None:
    """자녀 대시보드에서 코드를 찾을 수 있도록 최초 1회 기록을 남깁니다."""
    if not supabase:
        return
    session_key = f"registered_{parent_code}"
    if st.session_state.get(session_key):
        return
    try:
        existing = supabase.table("usage_logs")\
            .select("user_id")\
            .eq("user_id", parent_code)\
            .limit(1)\
            .execute()
        if not existing.data:
            supabase.table("usage_logs").insert({
                "user_id": parent_code,
                "question": "코드발급",
                "answer": "부모님 웹앱 코드가 발급되었습니다.",
                "has_image": False,
                "created_at": datetime.now().isoformat(),
            }).execute()
        st.session_state[session_key] = True
    except Exception:
        pass


def analyze_image(image: Image.Image, question: str) -> str:
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
            "어려운 용어 대신 쉬운 말로 설명하세요. "
            "화면의 위치, 색깔, 버튼 모양을 구체적으로 말하세요. "
            "한 번에 너무 많은 단계를 말하지 말고, 지금 바로 누를 곳을 먼저 알려주세요. "
            "개인정보, 결제, 송금, 비밀번호 입력 화면에서는 무리하게 진행시키지 말고 자녀나 직원에게 확인하라고 안내하세요."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[question, uploaded_image],
            config={"system_instruction": system_instruction},
        )
        return response.text or "답변을 만들지 못했어요. 사진을 조금 더 선명하게 다시 올려주세요."
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# =========================================================
# 화면 시작
# =========================================================
parent_code = get_or_create_parent_code()
register_code_once(parent_code)

st.markdown(
    """
<div class="title-area">
    <div class="title-main">🔗 이음이</div>
    <div class="title-sub">화면 사진 한 장이면 충분해요<br>디지털과 어르신을 잇다</div>
</div>
""",
    unsafe_allow_html=True,
)

if not GEMINI_API_KEY:
    st.error("⚠️ GEMINI_API_KEY가 없습니다. Streamlit Secrets 또는 .env에 키를 넣어주세요.")
    st.stop()

if not supabase:
    st.warning("⚠️ Supabase 연결 정보가 없어 사용 기록 저장과 자녀 대시보드 연결은 작동하지 않습니다.")

tab_help, tab_code = st.tabs(["📷 사진으로 물어보기", "👨‍👩‍👧 자녀 연결 코드"])

with tab_help:
    st.markdown("#### 📷 막히는 화면 사진을 올려주세요")
    st.markdown(
        """
<div class="guide-card">
키오스크, 병원 앱, 은행 앱, 기차 예매 화면처럼<br>
<b>어디를 눌러야 할지 모를 때 화면을 찍어서 올려주세요.</b><br>
AI가 쉬운 말로 다음 행동을 알려드립니다.
</div>
""",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "사진 선택",
        type=["jpg", "jpeg", "png"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="올린 화면", use_container_width=True)

        question = st.text_input(
            "궁금한 점",
            value="이 화면에서 다음에 뭘 누르면 되나요?",
            help="그냥 두셔도 됩니다.",
        )

        if st.button("✨ AI에게 물어보기"):
            with st.spinner("AI가 화면을 보고 있어요. 잠깐만 기다려주세요 🙏"):
                try:
                    answer = analyze_image(image, question)
                    save_log(parent_code, question, answer, has_image=True)
                    st.markdown("#### 📣 AI 답변")
                    st.markdown(f"<div class='answer-card'>{answer}</div>", unsafe_allow_html=True)
                except Exception as e:
                    err = f"오류가 발생했어요: {e}"
                    save_log(parent_code, question, err, has_image=True)
                    st.error(err)
    else:
        st.markdown(
            """
<div class="guide-card" style="text-align:center; padding:2rem;">
📱 위의 버튼을 눌러 화면 사진을 올리면<br>
AI가 <b>다음에 뭘 눌러야 하는지</b> 알려드려요.
</div>
""",
            unsafe_allow_html=True,
        )

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

    parent_url = get_parent_url(parent_code)
    st.text_input("부모님 휴대폰에 저장할 주소", value=parent_url)
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

st.markdown("---")
st.markdown(
    "<p style='text-align:center; color:#bbb; font-size:0.85rem;'>이음이 — 디지털과 어르신을 잇다</p>",
    unsafe_allow_html=True,
)
