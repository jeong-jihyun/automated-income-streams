---
name: smb-sns-caption-batch-generator
description: 매장 정보 JSON으로 한 달 치 SNS 글과 해시태그를 날짜별 CSV로 만들고 과장 표현을 점검하는 도구(자동 게시 없음). 사용자가 소상공인 SNS 문구 일괄 생성기 개발을 요청할 때 사용.
---
# PRJ-0039 소상공인 SNS 문구 일괄 생성기 (글 틀 기반)
`python -m snsgen <shop.json> --start YYYY-MM-DD --days 30 --out captions.csv`. 한계는 README 참고.
