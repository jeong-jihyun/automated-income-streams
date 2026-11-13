---
name: corporate-ai-training-workshop
description: 기업 AI 업무 활용 교육 워크숍의 견적·손익분기(인원별 손익, 합 보존 나눔)를 계산하고 업무별 AI 활용 체크리스트 점수를 내는 휴대폰용 오프라인 웹앱. 워크숍 가격·인원 계획이나 교육 대상 진단을 요청할 때 사용.
---
# 사용법
- app/index.html을 브라우저로 열면 샘플 값으로 결과가 바로 보인다.
- 계산 함수는 app/core.js: calcWorkshop(입력), splitCost(총액, 인원), breakEven(입력), scoreChecklist(답).
- 시험: node --test tests/test_all.js
- 한계: 실제 폰 설치·화면 확인 전. 세금·규정 미반영.
