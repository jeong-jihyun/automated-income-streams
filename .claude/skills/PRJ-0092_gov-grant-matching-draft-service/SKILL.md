---
name: gov-grant-matching-draft-service
description: 사업자 조건(업종·업력·지역·직원 수·대표 나이)과 샘플(가상) 지원사업 공고를 견줘 자격 일치·불일치 사유와 마감 임박순 정렬을 보여 주고, 선택한 공고의 신청서 초안(문단 틀)을 만드는 휴대폰용 오프라인 웹앱. 공고 매칭·신청서 초안 도구를 만들거나 규칙을 고칠 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`validateProfile`, `evaluate`, `rank`, `summarize`, `draftApplication`, `daysLeft`).
- 시험: `node --test tests/test_all.js`
- 한계: 공고는 직접 만든 가상 예시이며 실제 공고가 아니다. 외부 수집·제출 없음.
