---
name: booking-payment-mini-site-builder
description: 가게 설정 JSON으로 휴대폰용 소개 페이지, 중복 예약을 막는 예약 엔진, 취소·환불 계산, 시험용 결제와 시험 서버를 만드는 명령줄 도구. 사용자가 예약·결제 미니 사이트 제작을 요청할 때 사용.
---
1. `python -m booking_site check --config 설정.json`
2. `build`로 소개 페이지, `serve`로 시험 서버. 결제는 시험용이며 실제 결제 연동은 사람이 따로 해야 함.
