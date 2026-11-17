# 설계
- core.js: 순수 함수. 브라우저(window.Core)와 node(module.exports) 양쪽에서 쓴다.
- 입력: 업종, 지역(목록에서 선택), 업력(년, 0 이상), 직원 수(0 이상 정수), 대표 나이(15~100 정수), 오늘 날짜(YYYY-MM-DD). 오늘 날짜를 입력으로 받아 시험이 날짜에 흔들리지 않게 한다.
- 공고: id, name, agency, industries[], regions[](빈 목록 = 제한 없음), minBizYears/maxBizYears, minEmployees/maxEmployees, minRepAge/maxRepAge(없으면 제한 없음), deadline, amount(만 원), focus. 모두 가상 예시.
- 판정: 조건별로 일치 사유/불일치 사유를 모은다. 불일치가 하나라도 있으면 ineligible, 마감일이 지났거나 읽을 수 없으면 closed. 경계값은 포함.
- 마감: 남은 날 = 마감일 − 오늘 (UTC 일 수). 0이면 '오늘 마감'으로 아직 신청 가능. 7일 이내는 임박 표시.
- 정렬: eligible → ineligible → closed. 각 안에서 남은 날 오름차순, 같으면 id순. closed는 최근 마감 먼저.
- 초안: 7개 문단(개요, 자격 충족 사유, 동기, 추진 계획, 지원금 사용 계획, 기대 효과, 제출 전 확인). 모르는 값은 [ ] 빈칸. 자격 불일치·마감이면 경고 문구.
- 저장: localStorage 키 prj0092-v1, 읽기·쓰기 모두 try/catch.
