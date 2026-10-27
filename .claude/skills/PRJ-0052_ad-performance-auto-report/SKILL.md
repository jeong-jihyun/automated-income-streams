---
name: ad-performance-auto-report
description: 메타·네이버 광고 CSV를 합쳐 지난주 비교와 주의사항이 있는 주간 성과 보고서를 만드는 도구(API 연결 없음). 사용자가 SNS 광고 성과 자동 리포트 개발을 요청할 때 사용.
---
# PRJ-0052 SNS 광고 성과 자동 리포트 (주간 보고서 생성 도구)
`python -m adreport --meta <meta.csv> --naver <naver.csv> --week YYYY-MM-DD [--map 열이름.json] [--out 파일]`. 한계는 README 참고.
