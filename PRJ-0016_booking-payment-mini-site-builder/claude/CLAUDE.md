# PRJ-0016 작업 규칙
- 한국어, 쉬운 말. 실제 결제 연동·카드정보 저장 금지(시험용 흉내만). 한계를 README에 정직하게.
- 구조: booking_site/config.py engine.py(SQLite, UNIQUE 부분 인덱스로 중복 방지) payment.py(시험용) site.py server.py cli.py
- 스레드마다 별도 DB 연결로 시험. 테스트: python -m pytest -q
