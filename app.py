import os
import tempfile
import streamlit as st
from PIL import Image
from dotenv import load_dotenv
from google import genai

load_dotenv()

st.set_page_config(
    page_title="이음이 — 디지털 도우미",
    page_icon="🔗",
    layout="centered"
)

st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 20px !important;
}
[data-testid="stAppViewContainer"] {
    background-color: #FFF8F5;
}
[data-testid="stHeader"] {
    background-color: #FFF8F5;
}
.title-area {
    text-align: center;
    padding: 2rem 0 1rem 0;
}
.title-main {
    font-size: 4rem;
    font-weight: 900;
    color: #E8543A;
    letter-spacing: -1px;
    line-height: 1.1;
}
.title-sub {
    font-size: 1.4rem;
    color: #888;
    margin-top: 0.5rem;
}
h4 {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    margin-top: 1.5rem !important;
}
[data-testid="stFileUploader"] {
    background: #fff;
    border-radius: 16px;
    padding: 1.5rem;
    border: 3px dashed #F0C4B8;
}
[data-testid="stFileUploader"] label,
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
    font-size: 1.2rem !important;
}
[data-testid="stFileUploader"] button {
    font-size: 1.2rem !important;
    padding: 0.6rem 1.4rem !important;
    border-radius: 10px !important;
}
.stButton > button {
    background-color: #E8543A !important;
    color: white !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    padding: 1rem 2rem !important;
    border-radius: 16px !important;
    border: none !important;
    width: 100% !important;
    transition: background 0.2s;
    height: 4rem !important;
}
.stButton > button:hover {
    background-color: #C9422A !important;
}
.answer-card {
    background: #ffffff;
    border-left: 8px solid #E8543A;
    border-radius: 0 20px 20px 0;
    padding: 2rem 2.2rem;
    font-size: 1.6rem;
    line-height: 2.2;
    color: #222;
    margin-top: 1rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.guide-card {
    background: #FFF0EC;
    border-radius: 14px;
    padding: 1.5rem 1.8rem;
    font-size: 1.3rem;
    color: #555;
    margin-top: 0.5rem;
    line-height: 2.0;
}
.stTextInput > div > input {
    font-size: 1.3rem !important;
    padding: 0.8rem 1rem !important;
    border-radius: 12px !important;
    height: 3.2rem !important;
}
[data-testid="stSpinner"] p {
    font-size: 1.3rem !important;
}
[data-testid="stAlert"] p {
    font-size: 1.2rem !important;
}
hr {
    border: none;
    border-top: 2px solid #F0E8E4;
    margin: 1.8rem 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="title-area">
    <div class="title-main">🔗 이음이</div>
    <div class="title-sub">화면 사진 한 장이면 충분해요 — 디지털과 어르신을 잇다</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("⚠️ .env 파일에 GEMINI_API_KEY가 없어요. 키를 넣고 다시 실행해주세요.")
    st.stop()

st.markdown("#### 📷 화면 사진을 올려주세요")
st.markdown("""
<div class="guide-card">
키오스크, 병원 앱, 은행 앱, 기차 예매 화면 등<br>
<b>막히는 화면을 스마트폰으로 찍거나 캡처해서 올려주세요.</b>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    label="사진 선택",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed"
)

if uploaded_file:
    image = Image.open(uploaded_file)
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.image(image, caption="업로드된 화면", use_container_width=True)

    st.markdown("---")
    st.markdown("#### 💬 어떤 게 궁금하세요?")
    question = st.text_input(
        label="질문 입력",
        value="이 화면에서 다음에 뭘 누르면 되나요?",
        label_visibility="collapsed"
    )

    st.markdown(" ")
    ask_btn = st.button("✨  AI에게 물어보기")

    if ask_btn:
        with st.spinner("AI가 화면을 분석하고 있어요... 잠깐만요 🙏"):
            try:
                client = genai.Client()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                    image.convert("RGB").save(tmp.name, format="JPEG")
                    tmp_path = tmp.name

                uploaded_image = client.files.upload(file=tmp_path)
                os.unlink(tmp_path)

                system_instruction = (
                    "당신은 디지털 기기가 익숙하지 않은 어르신을 돕는 친절한 안내자입니다. "
                    "어려운 용어 대신 쉬운 말로, 짧고 명확하게 설명하세요. "
                    "예를 들어 '화면 오른쪽 아래 초록색 버튼을 눌러주세요'처럼 "
                    "위치와 색깔, 모양을 구체적으로 알려주세요. "
                    "한 번에 한 단계씩만 안내하고, 너무 길게 설명하지 마세요."
                )

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=[question, uploaded_image],
                    config={"system_instruction": system_instruction},
                )

                st.markdown("#### 📣 AI 답변")
                st.markdown(
                    f'<div class="answer-card">{response.text}</div>',
                    unsafe_allow_html=True
                )

            except Exception as e:
                st.error(f"오류가 발생했어요: {str(e)}")
else:
    st.markdown(" ")
    st.markdown("""
    <div class="guide-card" style="text-align:center; padding: 2rem;">
        📱 위의 버튼을 눌러 화면 사진을 올리면<br>
        AI가 <b>다음에 뭘 눌러야 하는지</b> 바로 알려드려요.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.markdown("""
<p style="text-align:center; color:#bbb; font-size:0.85rem;">
이음이 — 디지털과 어르신을 잇다
</p>
""", unsafe_allow_html=True)
