---
name: document-translation-localization-agency
description: 원문과 번역문을 문단별로 붙여 넣어 빈 문단·숫자·날짜·주소·고유명사 불일치·용어집 위반·길이 비율 이상·문단 수 불일치를 점검하고, 단어 수×단가+검수·재검수·서식으로 대행 견적(부가세 10%, 합계 보존)을 계산하는 휴대폰용 오프라인 웹앱(번역은 하지 않음). 번역 납품 검수·견적을 요청할 때 사용.
---
# 사용
- 화면: app/index.html. 계산: app/core.js (`splitParagraphs`, `parseGlossary`, `checkTranslation`, `countWords`, `quote`, `allocate`).
- 시험: `node --test tests/test_all.js`
- 한계: 번역·뜻 판단은 하지 않고, 고유명사는 영문 후보만 본다. 길이 비율 기준은 입력칸에서 바꾼다.
