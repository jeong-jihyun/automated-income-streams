# PRJ-0020 작업 규칙
- 한국어, 쉬운 말. 실제 플랫폼 API 형식·인증을 아는 척하지 말 것: 매핑은 '추정 예시'이며 README에 미확인 명시.
- 실제 연동·결제·자동 호출 기능 금지(채널 호출은 fetcher로 분리). 구조: kr_gateway/adapters.py gateway.py server.py cli.py
- 테스트: python -m pytest -q
