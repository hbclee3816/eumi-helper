import os
import tempfile
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from google import genai
from supabase import create_client
from datetime import datetime

load_dotenv()

# ─── Supabase 연결 (선택사항 — 없으면 로그 저장 안 됨) ────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

SYSTEM_INSTRUCTION = (
    "당신은 디지털 기기가 익숙하지 않은 어르신을 돕는 친절한 안내자입니다. "
    "어려운 용어 대신 쉬운 말로, 짧고 명확하게 설명하세요. "
    "예를 들어 '화면 오른쪽 아래 초록색 버튼을 눌러주세요'처럼 "
    "위치와 색깔, 모양을 구체적으로 알려주세요. "
    "한 번에 한 단계씩만 안내하고, 너무 길게 설명하지 마세요."
)

# ─── 서버 자동 깨우기 (14분마다 자기 자신에게 ping) ──────────
SERVER_URL = os.getenv("SERVER_URL", "https://eumi-helper.onrender.com")

async def keep_alive():
    """Render 무료 서버가 잠들지 않도록 14분마다 ping"""
    while True:
        await asyncio.sleep(14 * 60)  # 14분 대기
        try:
            async with httpx.AsyncClient() as http:
                await http.get(f"{SERVER_URL}/", timeout=10)
            print("✅ 서버 유지 ping 성공")
        except Exception as e:
            print(f"⚠️ ping 실패: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 시 자동 깨우기 백그라운드 실행
    asyncio.create_task(keep_alive())
    print("🔗 이음이 서버 시작 — 자동 유지 ON")
    yield

app = FastAPI(lifespan=lifespan)
client = genai.Client()


def kakao_response(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}]
        }
    }


async def save_log(user_id: str, question: str, answer: str, has_image: bool):
    """사용 기록을 Supabase에 저장 (자녀 대시보드용)"""
    if not supabase:
        return
    try:
        supabase.table("usage_logs").insert({
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "has_image": has_image,
            "created_at": datetime.now().isoformat()
        }).execute()
    except Exception as e:
        print(f"로그 저장 실패: {e}")


async def analyze_image_from_url(image_url: str, question: str) -> str:
    async with httpx.AsyncClient() as http:
        resp = await http.get(image_url)
        image_bytes = resp.content

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    uploaded_image = client.files.upload(file=tmp_path)
    os.unlink(tmp_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[question, uploaded_image],
        config={"system_instruction": SYSTEM_INSTRUCTION},
    )
    return response.text


@app.get("/")
def health_check():
    return {"status": "이음이 서버 정상 동작 중 🔗"}


@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
        user_request = body.get("userRequest", {})
        user_id = user_request.get("user", {}).get("id", "unknown")
        utterance = user_request.get("utterance", "").strip()
        attachments = user_request.get("attachment", {})

        # ── 이미지가 첨부된 경우 ─────────────────────────────
        if attachments and "image" in attachments:
            image_url = attachments["image"].get("url", "")
            question = utterance if utterance else "이 화면에서 다음에 뭘 누르면 되나요?"
            answer = await analyze_image_from_url(image_url, question)

            # 로그 저장
            await save_log(user_id, question, answer, has_image=True)

            return JSONResponse(content=kakao_response(answer))

        # ── 텍스트만 온 경우 ─────────────────────────────────
        if utterance:
            guide = (
                "안녕하세요! 이음이예요 🔗\n\n"
                "막히는 화면을 사진으로 찍어서 보내주세요.\n"
                "AI가 '여기 누르세요'처럼 쉽게 알려드릴게요! 📷"
            )
            await save_log(user_id, utterance, guide, has_image=False)
            return JSONResponse(content=kakao_response(guide))

        return JSONResponse(content=kakao_response(
            "사진을 보내주시면 바로 도와드릴게요! 📷"
        ))

    except Exception as e:
        print(f"오류 발생: {e}")
        return JSONResponse(content=kakao_response(
            "잠시 오류가 생겼어요. 다시 사진을 보내주세요 🙏"
        ))
