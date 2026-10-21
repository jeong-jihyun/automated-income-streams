# PRJ-0021 다채널 재고 동기화

여러 쇼핑몰의 재고를 **기준 재고 하나**로 맞추는 엔진입니다. 어느 채널에서 팔리든 기준 재고를 줄이고, 모든 채널에 "판매 가능 수량(기준 재고 − 안전재고)"을 다시 보냅니다. SQLite + 표준 라이브러리.

```bash
python -m inventory_sync --db inventory.db --config sample/config.json import --csv sample/stock.csv
python -m inventory_sync --db inventory.db --config sample/config.json sale e1 naver A-100 2
python -m inventory_sync --db inventory.db --config sample/config.json show
python -m pytest -q
```
- 같은 판매 알림(event_id)이 두 번 와도 한 번만 처리, 재고보다 많이 팔리면 `oversold`로 거부(재고는 음수가 안 됨).
- 채널 전송이 실패하면 기록하고 나머지는 계속, 다음 동기화 때 실패했던 채널만 다시 보냄. `reconcile`로 채널 실제 수량과 어긋난 곳을 찾음.

## 확인한 것 / 못 한 것
- 확인(테스트 10개): 마스터 차감과 전 채널 전파, 안전재고, 중복 알림, 과판매 거부, 변경 없을 때 재전송 안 함, 실패 채널 재시도, **15개 동시 판매에서 재고 10개면 정확히 10건만 성공**, 어긋남 감지, CSV·설정 오류 안내.
- **못 한 것**: **실제 쇼핑몰 API 연결 없음.** `pusher`(전송 함수)는 시험 출력일 뿐이며, 채널별 인증·재고 수정 API·웹훅 수신은 만들지 않았습니다(플랫폼 약관과 API 문서 확인 필요). 이미 채널에서 일어난 판매가 알림보다 늦게 오면 순간적인 과판매는 막을 수 없고, 안전재고와 `reconcile`로 줄이는 방식입니다. 구독 결제·화면(UI)·옵션 상품(색상/사이즈)·반품 입고는 없습니다.
