# CLAUDE.md (PRJ-0087 기업 AI 업무 활용 교육)
- 순수 HTML/CSS/JS. 외부 CDN·서버 호출·http 주소·결제·로그인 금지.
- 계산·판정은 app/core.js, 화면은 app/index.html, 모양은 app/style.css.
- core.js 끝에 module.exports 유지(시험용). 브라우저에서는 window.CORE.
- 돈은 정수 원 단위. 나누기는 splitCost로 하고 합 보존 시험을 깨지 않는다.
- 시험: `node --test tests/test_all.js` (Node 22는 폴더만 주면 실패).
- 저장은 localStorage(try/catch)만.
- 문서에는 코드에서 확인된 것만 적는다. 실제 폰 확인은 안 했다는 점을 유지.
