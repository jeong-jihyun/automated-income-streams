---
name: multichannel-inventory-sync
description: 기준 재고 하나로 여러 쇼핑몰 재고를 맞추는 엔진(중복 알림 방지, 과판매 거부, 안전재고, 실패 재시도, 어긋남 점검). 사용자가 다채널 재고 동기화 개발을 요청할 때 사용.
---
`python -m inventory_sync --config ... import|sale|show`. 실제 채널 전송은 pusher 함수를 사용자가 구현해야 함.
