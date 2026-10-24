# PRJ-0027 작업 규칙
- 한국어, 쉬운 말. admin_token은 코드·문서에 실제 값을 쓰지 않는다(예시 값만). origins에 '*' 금지.
- 구조: form_backend/core.py(검사·제한·댓글·관리) server.py(HTTP) cli.py. 테스트: python -m pytest -q
