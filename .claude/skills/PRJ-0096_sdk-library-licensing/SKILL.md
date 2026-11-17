---
name: sdk-library-licensing
description: 라이선스 키(형식·단순 검사값·만료·좌석)를 판정하고, 좌석 구간 단가·지원 등급·다년 할인·부가세 10% 연간 라이선스 견적과 갱신 안내일(만료 60/30/7일 전)을 계산하는 휴대폰용 오프라인 웹앱(법률 자문 아님, 단가 예시). SDK·라이브러리 라이선스 도구를 만들거나 고칠 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`checkLicense`, `makeKey`, `parseKey`, `quote`, `renewalSchedule`, `allocate`).
- 시험: `node --test tests/test_all.js`
- 한계: 검사값은 암호 보안이 아니다. 단가·할인율은 core.js 상단의 SEAT_TIERS, SUPPORT, MULTI_DISCOUNT 예시값이며 바꿔 쓴다. 날짜는 '오늘' 입력값 기준.
