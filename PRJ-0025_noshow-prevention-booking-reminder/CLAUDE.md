# PRJ-0025 작업 규칙
- 한국어, 쉬운 말. 실제 문자 발송 자동화 금지(sender 주입). 문자 관련 법적 요건은 미확인으로 README에 유지.
- 구조: noshow/core.py(예약·알림·답장·대기자·노쇼) cli.py. 노쇼는 직원이 mark_done 하지 않은 지난 예약. 테스트: python -m pytest -q
