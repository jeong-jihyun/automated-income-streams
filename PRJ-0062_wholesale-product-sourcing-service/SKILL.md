---
name: wholesale-product-sourcing-service
description: 도매 상품 CSV를 정리해 판매가(수수료·마진 반영)를 계산하고 등록용 CSV와 보류 목록을 만드는 도구(수집·자동 등록 없음). 사용자가 도매 상품 수집·등록 대행 도구 개발을 요청할 때 사용.
---
# PRJ-0062 도매 상품 수집·등록 대행 (도매 상품 정리·판매가 계산 도구)
`python -m wholesale <도매.csv> [--config 설정.json] [--out ok.csv] [--hold hold.csv]`. 한계는 README 참고.
