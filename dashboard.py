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
</style>
""", unsafe_allow_html=True)

# ─── 헤더 ───────────────────────────────────────────────────
st.markdown("""
<h1 style='color:#E8543A; font-size:2.5rem; margin-bottom:0;'>🔗 이음이</h1>
<p style='color:#888; font-size:1.2rem;'>자녀용 케어 대시보드 — 부모님 디지털 사용 현황</p>
<hr style='border:1px solid #F0E8E4;'>
""", unsafe_allow_html=True)

# ─── Supabase 연결 ──────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("⚠️ .env 파일에 SUPABASE_URL과 SUPABASE_KEY를 넣어주세요.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── 데이터 불러오기 ────────────────────────────────────────
@st.cache_data(ttl=60)
def load_logs():
    try:
        result = supabase.table("usage_logs")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(100)\
            .execute()
        return result.data
    except:
        return []

logs = load_logs()

if not logs:
    st.markdown("""
    <div style='text-align:center; padding:3rem; color:#aaa; font-size:1.3rem;'>
        📱 아직 사용 기록이 없어요.<br>
        부모님이 이음이에 사진을 보내시면 여기에 표시돼요!
    </div>
    """, unsafe_allow_html=True)
else:
    df = pd.DataFrame(logs)
    df["created_at"] = pd.to_datetime(df["created_at"])

    # ─── 요약 카드 ─────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    today = datetime.now().date()
    today_logs = [l for l in logs if l["created_at"][:10] == str(today)]
    image_logs = [l for l in logs if l.get("has_image")]
    week_logs = [l for l in logs if
        datetime.fromisoformat(l["created_at"]).date() >= today - timedelta(days=7)]

    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <p style='color:#888; font-size:1rem; margin:0;'>오늘 질문 횟수</p>
            <p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(today_logs)}번</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <p style='color:#888; font-size:1rem; margin:0;'>이번 주 총 사용</p>
            <p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(week_logs)}번</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <p style='color:#888; font-size:1rem; margin:0;'>사진으로 질문한 횟수</p>
            <p style='color:#E8543A; font-size:2.5rem; font-weight:700; margin:0;'>{len(image_logs)}번</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ─── 최근 사용 기록 ─────────────────────────────────────
    st.markdown("#### 📋 최근 사용 기록")

    for log in logs[:20]:
        time_str = datetime.fromisoformat(log["created_at"]).strftime("%m월 %d일 %H:%M")
        icon = "📷" if log.get("has_image") else "💬"
        question = log.get("question", "")
        answer = log.get("answer", "")[:100] + "..." if len(log.get("answer", "")) > 100 else log.get("answer", "")

        st.markdown(f"""
        <div class='log-card'>
            <p style='color:#888; font-size:0.9rem; margin:0 0 0.3rem;'>{icon} {time_str}</p>
            <p style='font-weight:600; margin:0 0 0.3rem;'>질문: {question}</p>
            <p style='color:#555; margin:0;'>답변: {answer}</p>
        </div>
        """, unsafe_allow_html=True)

# ─── 새로고침 버튼 ──────────────────────────────────────────
st.markdown("---")
if st.button("🔄 새로고침"):
    st.cache_data.clear()
    st.rerun()

st.markdown("""
<p style='text-align:center; color:#ccc; font-size:0.85rem;'>
이음이 — 디지털과 어르신을 잇다
</p>
""", unsafe_allow_html=True)
