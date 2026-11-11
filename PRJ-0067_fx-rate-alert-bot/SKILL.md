---
name: fx-rate-alert-bot
description: 환율·금리 규칙과 시세 CSV로 기준가 도달 알림을 판정하고 중복 없이 outbox 파일에 쌓는 도구(수집·전송 없음). 사용자가 환율·금리 알림 봇 개발을 요청할 때 사용.
---
# PRJ-0067 환율·금리 알림 봇 (기준가 도달 판정 도구)
`python -m fxalert <rules.json> <readings.csv> [--state state.json] [--outbox outbox.jsonl] [--now ISO시각]`. 한계는 README 참고.
