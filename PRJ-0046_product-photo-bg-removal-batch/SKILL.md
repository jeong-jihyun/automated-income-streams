---
name: product-photo-bg-removal-batch
description: 폴더의 상품 사진 배경(단순한 단색)을 흰색으로 바꾸고 규격에 맞춰 일괄 저장하며 실패 사유를 보고서로 남기는 도구. 사용자가 상품 사진 배경 제거 대량 처리 서비스 개발을 요청할 때 사용.
---
# PRJ-0046 상품 사진 배경 제거·보정 대량 처리 (단순 배경 전용)
`python -m photobatch <입력폴더> <출력폴더> --preset square_1000|market_800|wide_1200x900 --color white|gray [--dry-run]`. 한계는 README 참고.
