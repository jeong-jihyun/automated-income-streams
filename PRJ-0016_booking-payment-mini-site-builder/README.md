# PRJ-0016 예약·결제 미니 사이트 빌더

가게 설정 JSON → **휴대폰용 소개 페이지 + 예약 엔진(중복 예약 방지) + 취소·환불 금액 계산 + 시험용 결제 흉내**를 만들고, 시험용 서버로 눌러볼 수 있습니다.
**실제 결제는 연결하지 않았습니다.** 돈이 오가지 않으며, 시험 카드번호(4242…)만 받습니다.
설계 문서의 Next.js 대신 **파이썬 표준 라이브러리 + SQLite**로 만든 시험용 버전입니다.

## 실행
```bash
python -m booking_site check --config sample/shop.json
python -m booking_site build --config sample/shop.json --out output      # 소개 페이지(index.html)
python -m booking_site serve --config sample/shop.json --port 8000       # 시험용 서버 (Ctrl+C로 끔)
python -m pytest -q
```
API(시험용): `GET /api/slots?date=YYYY-MM-DD`, `POST /api/book {slot,service,name}`, `POST /api/pay {id,card}`, `POST /api/cancel {id}`

## 확인한 것 / 못 한 것
- 확인(테스트 11개): 같은 시간 중복 예약 차단(스레드 8개 동시 시도에서 1명만 성공), 지난 시간·없는 서비스 거부, 환불 단계 경계값(48시간 정각/1분 뒤 등), 결제 후 취소 시 환불액, 취소하면 다시 예약 가능, 실제 서버를 띄워 요청 주고받기, 설정 오류 안내, 소개 페이지의 viewport·HTML 이스케이프.
- **못 한 것**: 실제 결제 연동(토스·카카오페이 등)은 없음. 로그인·관리자 화면·알림·예약 화면(폼) UI는 없음(소개 페이지의 "예약하기"는 `/book` 페이지가 아직 없음). 실제 휴대폰에서의 모양, 여러 사람이 동시에 쓰는 운영 환경, 시간대(서버 현지 시각 기준) 처리는 확인하지 않았습니다. 환불 규정은 예시이며 실제 영업에서는 전자상거래법 등 규정을 사람이 확인해야 합니다.
