# CLAUDE.md (PRJ-0088 계약서·서류 템플릿 자동 생성 시스템)

- 순수 HTML/CSS/JS. 외부 CDN·서버 호출·http 주소·결제·로그인 금지.
- 계산·판정은 `app/core.js`에만 둔다. `app/index.html`은 `window.Core`를 불러 화면만 그린다.
- 저장은 localStorage(try/catch)만. 키: `prj0088_state_v1`.
- 새 서류는 `core.js`의 `TEMPLATES`에 추가(fields, body의 `{{칸}}`·`{{금액칸_한글}}`, rules)하고 `SAMPLES`에 샘플을 넣는다.
- 시험: `node --test tests/test_all.js` (Node 22에서 `tests/` 폴더 인자는 실패함).
- 항상 "법률 자문 아님" 문구를 보여 준다. 법적 판단을 단정하지 않는다.
- 이 폴더 밖 파일 수정, git·시트·알림·블로그 작업은 하지 않는다.
