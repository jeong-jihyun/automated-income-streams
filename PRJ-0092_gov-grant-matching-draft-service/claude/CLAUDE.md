# CLAUDE.md
- 항목: PRJ-0092 정부지원사업 공고 매칭·신청서 초안 서비스.
- 핵심 판정은 app/core.js, 화면은 app/index.html + style.css. 외부 CDN·서버 호출·http 주소 금지.
- 공고는 core.js의 SAMPLE_GRANTS(가상 예시). 실제 공고처럼 보이게 바꾸지 않고, 화면의 '가상 예시' 안내를 지우지 않는다.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 시험: `node --test tests/test_all.js`. 기준값 경계는 포함(이상/이하), 마감일 당일은 신청 가능.
- 폴더 밖 파일은 건드리지 않는다.
