---
name: survey-auto-report-saas
description: 설문 응답 CSV를 점검해 열 종류별 집계(평균·분포·키워드), 개인정보 열 제외, HTML(막대그래프)·PDF 보고서를 만드는 명령줄 도구. 사용자가 설문 결과 자동 리포트를 요청할 때 사용.
---
1. `python -m survey_report check --csv 파일.csv` 로 열 종류·개인정보 의심 열 확인
2. `python -m survey_report build --csv 파일.csv --out output --title 제목`
3. 개인정보 열은 기본 제외. 주관식은 단어 빈도일 뿐이니 해석은 사람이 확인.
