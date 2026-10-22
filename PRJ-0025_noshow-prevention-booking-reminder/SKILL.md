---
name: noshow-prevention-booking-reminder
description: 예약 확인 알림(24h/2h 전), 답장 처리, 취소 시 대기자 자동 제안, 노쇼 집계를 하는 로컬 도구(문자는 실제로 보내지 않음). 사용자가 노쇼 방지 예약 알림 개발을 요청할 때 사용.
---
`python -m noshow --config ... add|wait|remind|reply`. 문자 발송 연동은 sender 함수를 사용자가 구현.
