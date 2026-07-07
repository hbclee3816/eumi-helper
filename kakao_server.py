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

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SERVER_URL = os.getenv("SERVER_URL", "https://eumi-helper.onrender.com")

# Supabase는 없어도 서버가 죽지 않게 처리
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Supabase 연결 준비 완료")
    except Exception as e:
        print(f"⚠️ Supabase 초기화 실패: {e}")
else:
    print("⚠️ SUPABASE_URL 또는 SUPABASE_KEY가 없습니다. 로그 저장은 건너뜁니다.")

if GEMINI_API_KEY:
    print("✅ GEMINI_API_KEY 확인 완료")
else:
    print("⚠️ GEMINI_API_KEY가 없습니다. 이미지 분석은 동작하지 않습니다.")

SYSTEM_INSTRUCTION = (
    "당신은 디지털 기기가 익숙하지 않은 어르신을 돕는 친절한 안내자입니다. "
    "어려운 용어 대신 쉬운 말로, 짧고 명확하게 설명하세요. "
    "예를 들어 '화면 오른쪽 아래 초록색 버튼을 눌러주세요'처럼 "
    "위치와 색깔, 모양을 구체적으로 알려주세요. "
    "한 번에 한 단계씩만 안내하고, 너무 길게 설명하지 마세요."
)


async def keep_alive():
    """Render 무료 서버가 잠들지 않도록 14분마다 ping"""
    while True:
        await asyncio.sleep(14 * 60)
        try:
            async with httpx.AsyncClient() as http:
                await http.get(f"{SERVER_URL}/", timeout=10)
            print("✅ 서버 유지 ping 성공")
        except Exception as e:
            print(f"⚠️ ping 실패: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(keep_alive())
    print("🔗 이음이 서버 시작 — 자동 유지 ON")
    yield


app = FastAPI(lifespan=lifespan)


def get_gemini_client():
    """GEMINI_API_KEY 오류 때문에 서버 전체가 죽지 않도록 필요할 때만 생성"""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY가 Render 환경변수에 없습니다.")
    return genai.Client(api_key=GEMINI_API_KEY)


def kakao_response(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [{"simpleText": {"text": text}}]
        }
    }


async def save_log(user_id: str, question: str, answer: str, has_image: bool):
    if not supabase:
        print("⚠️ Supabase 미연결 — 로그 저장 생략")
        return
    try:
        supabase.table("usage_logs").insert({
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "has_image": has_image,
            "created_at": datetime.now().isoformat()
        }).execute()
        print("✅ 로그 저장 완료")
    except Exception as e:
        print(f"⚠️ 로그 저장 실패: {e}")


def find_image_url(body: dict) -> str:
    """카카오 요청 구조가 조금 달라도 이미지 URL을 최대한 찾아냄"""
    user_request = body.get("userRequest", {}) or {}
    action = body.get("action", {}) or {}
    params = action.get("params", {}) or {}

    candidates = [
        user_request.get("attachment", {}),
        user_request.get("attachments", {}),
        params.get("attachment", {}),
        params.get("attachments", {}),
        params,
    ]

    for item in candidates:
        if isinstance(item, dict):
            if "image" in item and isinstance(item["image"], dict):
                url = item["image"].get("url") or item["image"].get("secure_url")
                if url:
                    return url
            for key in ["imageUrl", "image_url", "url"]:
                if item.get(key):
                    return item.get(key)
    return ""


async def analyze_image_from_url(image_url: str, question: str) -> str:
    if not image_url:
        return "사진 주소를 찾지 못했어요. 사진을 다시 보내주세요."

    async with httpx.AsyncClient() as http:
        resp = await http.get(image_url, timeout=20)
        resp.raise_for_status()
        image_bytes = resp.content

    tmp_path = ""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            tmp.write(image_bytes)
            tmp_path = tmp.name

        client = get_gemini_client()
        uploaded_image = client.files.upload(file=tmp_path)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[question, uploaded_image],
            config={"system_instruction": SYSTEM_INSTRUCTION},
        )
        return response.text or "화면을 분석했지만 답변을 만들지 못했어요. 사진을 다시 보내주세요."
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.get("/")
def health_check():
    return {"status": "이음이 서버 정상 동작 중 🔗"}


@app.get("/debug")
def debug_check():
    return {
        "server": "ok",
        "gemini_key": bool(GEMINI_API_KEY),
        "supabase_url": bool(SUPABASE_URL),
        "supabase_key": bool(SUPABASE_KEY),
        "server_url": SERVER_URL,
    }


@app.post("/webhook")
async def webhook(request: Request):
    try:
        body = await request.json()
        print("✅ WEBHOOK HIT")
        print(f"📩 KAKAO BODY: {body}")

        user_request = body.get("userRequest", {}) or {}
        user_id = user_request.get("user", {}).get("id", "unknown")
        utterance = (user_request.get("utterance", "") or "").strip()
        image_url = find_image_url(body)

        # ── 내 코드 요청 ─────────────────────────────────────
        if utterance.replace(" ", "") in ["내코드", "코드", "내코드알려줘"]:
            code_msg = (
                f"안녕하세요! 이음이예요 🔗\n\n"
                f"자녀분께 전달할 코드예요:\n\n"
                f"📋 {user_id}\n\n"
                f"자녀분이 이음이 대시보드에서\n"
                f"이 코드를 입력하면 연결돼요!"
            )
            await save_log(user_id, "내코드", code_msg, has_image=False)
            return JSONResponse(content=kakao_response(code_msg))

        # ── 이미지가 첨부된 경우 ─────────────────────────────
        if image_url:
            question = utterance if utterance else "이 화면에서 다음에 뭘 누르면 되나요?"
            answer = await analyze_image_from_url(image_url, question)
            await save_log(user_id, question, answer, has_image=True)
            return JSONResponse(content=kakao_response(answer))

        # ── 텍스트만 온 경우 ─────────────────────────────────
        if utterance:
            guide = (
                "안녕하세요! 이음이예요 🔗\n\n"
                "막히는 화면을 사진으로 찍어서 보내주세요.\n"
                "AI가 '여기 누르세요'처럼 쉽게 알려드릴게요! 📷\n\n"
                "자녀분과 연결하고 싶으시면\n'내코드' 라고 보내주세요!"
            )
            await save_log(user_id, utterance, guide, has_image=False)
            return JSONResponse(content=kakao_response(guide))

        return JSONResponse(content=kakao_response(
            "사진을 보내주시면 바로 도와드릴게요! 📷"
        ))

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return JSONResponse(content=kakao_response(
            "잠시 오류가 생겼어요. 다시 사진을 보내주세요 🙏"
        ))
