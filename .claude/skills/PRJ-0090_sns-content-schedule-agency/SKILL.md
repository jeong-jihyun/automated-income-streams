---
name: sns-content-schedule-agency
description: SNS 게시 계획(날짜, 채널, 제목)을 점검(같은 날 같은 채널 중복, 빈 날, 주당 게시 수, 요일 쏠림)하고 월 달력과 대행 월 견적(부가세 10%, 합계 보존)을 보여 주는 휴대폰용 웹앱. 자동 게시 없음.
---

# SNS 콘텐츠 일정 관리 대행

- 앱: `app/index.html` (core.js, style.css 사용). 브라우저에서 바로 열면 된다.
- 계산: `app/core.js` 의 `parsePlan`, `analyze`, `buildCalendar`, `allocate`, `quote`.
- 시험: `node --test tests/test_all.js`
- 한계: 실제 폰 설치·화면 미확인. 공휴일, 채널별 단가 미지원.
