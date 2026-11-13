# CLAUDE.md - PRJ-0089 고객 문의 접수·분류 구축

## 구조
- `app/core.js`: 핵심 계산 전부 (분류·긴급도·묶기·규칙 글 읽기). 브라우저에서는 `window.InquiryCore`, node에서는 `require`로 쓴다. 파일 끝에 `module.exports`.
- `app/index.html`: 화면과 이벤트만. 계산은 core.js 호출.
- `app/style.css`: 큰 글씨, 세로 화면, 어두운 모드.
- `tests/test_all.js`: node:test. 실행은 `node --test tests/test_all.js`.

## 지킬 것
- 외부 CDN·http 주소·fetch 등 네트워크 호출 금지 (시험이 검사한다). 전송·결제·로그인 기능 금지.
- 저장은 localStorage만, 항상 try/catch. 키는 `prj0089-state-v1`.
- 규칙 형식: `칸 이름: 키워드, 키워드` 한 줄 하나. 동점이면 앞 칸이 이긴다. 키워드가 없으면 `기타(담당 미정)`.
- 글은 한국어, 쉬운 말. 화면에 사용자 입력을 넣을 때는 textContent로만 (innerHTML 금지).
- core.js를 고치면 시험을 돌려 통과시킨다.
