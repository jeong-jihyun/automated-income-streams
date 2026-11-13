---
name: contract-template-auto-generator
description: 용역 계약서·임대차 계약서·차용증 템플릿의 빈칸을 채워 문서 초안을 만들고, 빈 칸·금액 한글 표기·대금 합계·날짜 순서 오류를 점검하는 오프라인 휴대폰 웹앱(법률 자문 아님). 계약서 템플릿 자동 생성 도구 개발·수정·시험을 요청할 때 사용.
---

# 사용법
- 앱: `app/index.html` (core.js, style.css). 서버 불필요.
- 핵심 함수(`app/core.js`): `build(id, values)`, `validate`, `render`, `moneyToHangul`, `splitPayment`, `parseDate`.
- 템플릿 id: `service`, `lease`, `loan`.
- 시험: `node --test tests/test_all.js`
- 규칙: 외부 연결 금지, 법률 자문 아님 문구 유지, 확인한 것만 문서에 적기.
