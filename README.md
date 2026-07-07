# 이음이 웹앱 MVP

카카오 오픈빌더 방식은 보류하고, 부모님이 웹주소에 접속해서 사진을 올리면 AI가 안내하는 방식으로 전환한 버전입니다.

## 파일 구성

- `app.py` : 부모님용 웹앱. 사진 업로드, AI 답변, 자녀 연결 코드 발급
- `dashboard.py` : 자녀용 대시보드. 로그인, 부모님 연결, 사용 기록 확인
- `requirements.txt` : 설치 패키지
- `Procfile` : Render에서 Streamlit으로 실행할 때 사용
- `.env.example` : 환경변수 예시
- `.gitignore` : 비밀키 업로드 방지
- `supabase_setup.sql` : Supabase 테이블/정책 예시

## 환경변수

Streamlit Cloud 또는 Render 환경변수에 아래를 넣으세요.

```text
GEMINI_API_KEY
SUPABASE_URL
SUPABASE_KEY
APP_URL
PARENT_APP_URL
```

`APP_URL`과 `PARENT_APP_URL`은 부모님용 웹앱 주소입니다.

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

자녀 대시보드는 별도 앱으로 배포하거나 아래처럼 실행합니다.

```bash
streamlit run dashboard.py
```

## 운영 방향

1. 카카오톡 채널은 삭제하지 말고, 웹앱 링크 안내용으로만 사용합니다.
2. 카카오 오픈빌더, FastAPI 웹훅, Render webhook 방식은 일단 중단합니다.
3. 부모님 휴대폰 홈 화면에 이음이 웹앱 링크를 추가해서 사용합니다.
4. 자녀는 대시보드에서 부모님 연결 코드를 입력해 사용 기록을 확인합니다.
