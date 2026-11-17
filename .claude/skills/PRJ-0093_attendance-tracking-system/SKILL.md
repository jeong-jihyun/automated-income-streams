---
name: attendance-tracking-system
description: 직원별 출퇴근 시각 여러 줄 글에서 근무시간·휴게 차감·연장·야간·지각·조퇴·누락(출근만/퇴근만) 경고를 계산하고 직원별 월 합계와 시급 곱한 급여 참고 합계(합계 보존)를 보여 주는 휴대폰용 오프라인 웹앱(세법·노동법 자문 아님, 기준값은 예시). 근태 집계 도구를 만들거나 고치거나 시험할 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`parseRecords`, `calcDay`, `nightOverlap`, `summarize`, `allocate`, `parseWages`).
- 시험: `node --test tests/test_all.js`
- 한계: 기준값은 입력칸에서 바꾸는 예시값이다. 주휴수당·보험·세금 공제는 계산하지 않는다. 지각·조퇴는 소정 근무 시간대 안에서 시작한 근무에만 판정한다.
