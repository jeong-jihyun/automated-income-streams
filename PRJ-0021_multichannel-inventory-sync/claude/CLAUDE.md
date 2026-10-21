# PRJ-0021 작업 규칙
- 한국어, 쉬운 말. 실제 쇼핑몰 API 자동 호출 기능 금지(pusher는 주입식). 한계는 README에 정직하게.
- 구조: inventory_sync/core.py(sale·sync·reconcile) cli.py. 재고 차감은 한 SQL(UPDATE … WHERE stock>=qty)로 해서 동시 판매에도 안전.
- 테스트: python -m pytest -q
