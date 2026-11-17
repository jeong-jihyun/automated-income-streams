---
name: opensource-dual-license-sales
description: 사용자 유형·직원 수·SaaS 재배포 여부로 무료/유료/문의 판정을 하고, 직원 수 구간·개발자 수·다년 할인으로 라이선스 견적(부가세 10%, 합계 보존)을 내며, 기여자 동의(CLA) 점검과 이중 라이선스 불가 경고를 보여 주는 오프라인 휴대폰 웹앱(법률 자문 아님). 오픈소스 이중 라이선스 판매 준비를 요청할 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`judge`, `quote`, `claCheck`, `parseTiers`, `allocate`).
- 시험: `node --test tests/test_all.js`
- 한계: 구간·단가·할인율은 예시값이며 입력칸에서 바꾼다. 법률 자문이 아니다.
