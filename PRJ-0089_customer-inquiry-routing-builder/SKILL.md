---
name: customer-inquiry-routing-builder
description: 고객 문의 여러 줄을 키워드 규칙으로 담당 칸(배송·환불·교환·결제·사용법 등)에 나누고 화난 표현·기한 표현으로 긴급도를 매겨 칸별로 정렬하는 오프라인 휴대폰용 웹앱(전송 기능 없음). 문의 접수·분류 도구를 만들거나 규칙을 고칠 때 사용.
---

# 고객 문의 접수·분류 구축

- 앱: `app/index.html` (core.js, style.css). 브라우저로 열면 샘플이 들어 있고 [분류하기]로 결과를 본다.
- 규칙 고치기: 화면의 [분류 규칙 고치기] 또는 `app/core.js`의 `DEFAULT_RULES`, `DEFAULT_URGENCY`.
- 시험: `node --test tests/test_all.js`
- 한계: 키워드 일치 방식이라 부정문·문맥을 이해하지 못한다. 실제 폰 설치·화면은 확인하지 않았다.
