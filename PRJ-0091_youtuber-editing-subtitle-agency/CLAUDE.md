# CLAUDE.md
- 항목: PRJ-0091 유튜버용 영상 편집·자막 대행 (업무자동화).
- 핵심 계산은 app/core.js, 화면은 app/index.html + style.css. 외부 CDN·서버 호출·http 주소 금지.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 시험: `node --test tests/test_all.js`. 돈 계산은 항목 합 = 총합이 되도록 allocate()로 나머지를 처리한다.
- 폴더 밖 파일은 건드리지 않는다.
