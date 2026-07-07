# 이음이 웹앱

## 이번 버전 핵심

- 카카오 오픈빌더/챗봇 방식 중단
- 부모님용 웹앱(app.py)과 자녀용 대시보드(dashboard.py) 분리
- 부모님도 휴대폰 번호 + 비밀번호로 가입/로그인
- 부모님 질문 기록을 계속 저장
- AI가 질문을 자동 분류
  - 큰 분류: 키오스크, 병원 앱, 은행 앱 등
  - 장소/앱: 맥도날드, 코레일, 국민은행 등
  - 하려는 일: 주문하기, 결제하기, 예매하기 등
- 같은 장소/분류의 이전 기록을 찾아서 답변에 참고
- 자녀는 부모님 연결 코드를 입력해서 사용 기록 확인

## GitHub에 올릴 파일

- app.py
- dashboard.py
- requirements.txt
- Procfile
- README.md
- supabase_setup.sql
- .env.example
- .gitignore
- .streamlit/config.toml

## GitHub에 절대 올리면 안 되는 파일

- .env

## Streamlit Secrets 필수값

부모님용 app.py 앱과 자녀용 dashboard.py 앱 모두 아래 값을 넣는 것을 권장합니다.

```toml
GEMINI_API_KEY = "실제 Gemini API 키"
SUPABASE_URL = "https://프로젝트.supabase.co"
SUPABASE_KEY = "Supabase anon/publishable key"
SUPABASE_SERVICE_ROLE_KEY = "Supabase service_role key"
AUTH_SECRET = "긴 랜덤 문자열"
APP_URL = "https://eumi-parent.streamlit.app"
PARENT_APP_URL = "https://eumi-parent.streamlit.app"
```

중요: SUPABASE_SERVICE_ROLE_KEY는 GitHub에 올리면 안 됩니다. Streamlit Secrets에만 넣으세요.

## Supabase 설정

1. Supabase > SQL Editor
2. supabase_setup.sql 전체 실행
3. 이번 버전은 Supabase Auth 이메일 회원가입을 사용하지 않습니다.
4. 그래서 Email Provider / Phone Provider 설정은 회원가입 오류와 직접 관련이 없습니다.

## 앱 구성

### 부모님용 앱

- Main file path: app.py
- 부모님 회원가입/로그인
- 사진 질문
- 내 기록 보기
- 자녀 연결 코드 보기

### 자녀용 앱

- Main file path: dashboard.py
- 자녀 회원가입/로그인
- 부모님 코드 연결
- 장소별 기록 보기
- 자주 어려워한 화면 확인

## 카카오 채널 사용법

카카오 채널은 삭제하지 말고, 웹앱 링크 안내용으로만 사용합니다.

예시 문구:

이음이 이용하기  
아래 주소를 눌러 화면 사진을 올려주세요.  
AI가 다음에 무엇을 눌러야 하는지 쉽게 알려드립니다.  
https://eumi-parent.streamlit.app
