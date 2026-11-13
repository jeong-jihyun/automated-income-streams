# PRJ-0090 SNS 콘텐츠 일정 관리 대행

- 순수 HTML/CSS/JS. 외부 CDN, 서버 호출, http 주소, 결제, 로그인, 전송 금지.
- 계산·판정은 `app/core.js` 에만 둔다. `app/index.html` 은 `window.SnsCore` 를 불러 화면만 그린다.
- core.js 끝은 브라우저(`window.SnsCore`)와 node(`module.exports`) 겸용 구조.
- 저장은 localStorage(키 `prj0090-state`)만, 항상 try/catch.
- 시험: `node --test tests/test_all.js`. 돈 계산 합계 보존 시험을 지우지 않는다.
- 사용자 글 출력은 `esc()` 로 이스케이프한다.
- 이 폴더 밖 파일은 건드리지 않는다.
