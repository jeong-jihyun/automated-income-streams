---
name: smartstore-bulk-listing-tool
description: 엑셀·CSV 상품 목록을 등록 전에 행·열별로 검수하고 통과한 상품만 정리된 CSV로 내보내는 도구(업로드 없음, 기준은 예시). 사용자가 스마트스토어 상품 등록 자동화 도구 개발을 요청할 때 사용.
---
# PRJ-0061 스마트스토어 상품 등록 자동화 도구 (일괄 등록 전 검수·정리 도구)
`python -m bulklist <상품.xlsx|csv> --categories <코드.json> [--out ok.csv] [--errors errors.csv]`. 한계는 README 참고.
