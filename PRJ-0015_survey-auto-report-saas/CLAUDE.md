# PRJ-0015 작업 규칙
- 한국어, 쉬운 말. 유료 API·네트워크 사용 금지(표준 라이브러리 + reportlab). 개인정보 열은 기본 제외.
- 웹 서비스/결제/로그인 기능은 범위 밖. 한계는 README에 정직하게.
- 구조: survey_report/analyze.py(집계·개인정보) render.py(HTML·SVG·PDF) cli.py. 테스트: python -m pytest -q
