import os
import tempfile
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from google import genai

load_dotenv()

app = FastAPI()
client = genai.Client()

SYSTEM_INSTRUCTION = (
    "당신은 디지털 기기가 익숙하지 않은 어르신을 돕는 친절한 안내자입니다. "
    "어려운 용어 대신 쉬운 말로, 짧고 명확하게 설명하세요. "
    "예를 들어 '화면 오른쪽 아래 초록색 버튼을 눌러주세요'처럼 "
    "위치와 색깔, 모양을 구체적으로 알려주세요. "
    "한 번에 한 단계씩만 안내하고, 너무 길게 설명하지 마세요."
)


def kakao_response(text: str) -> dict:
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {"simpleText": {"text": text}}
            ]
        }
    }


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
        utterance = user_request.get("utterance", "").strip()
        attachments = user_request.get("attachment", {})

        if attachments and "image" in attachments:
            image_url = attachments["image"].get("url", "")
            question = utterance if utterance else "이 화면에서 다음에 뭘 누르면 되나요?"
            answer = await analyze_image_from_url(image_url, question)
            return JSONResponse(content=kakao_response(answer))

        if utterance:
            guide = (
                "안녕하세요! 이음이예요 🔗\n\n"
                "막히는 화면을 사진으로 찍어서 보내주세요.\n"
                "AI가 '여기 누르세요'처럼 쉽게 알려드릴게요! 📷"
            )
            return JSONResponse(content=kakao_response(guide))

        return JSONResponse(content=kakao_response(
            "사진을 보내주시면 바로 도와드릴게요! 📷"
        ))

    except Exception as e:
        print(f"오류 발생: {e}")
        return JSONResponse(content=kakao_response(
            "잠시 오류가 생겼어요. 다시 사진을 보내주세요 🙏"
        ))
