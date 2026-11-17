# CLAUDE.md
- 항목: PRJ-0095 오픈소스 이중 라이선스 판매 (개인 무료, 기업 상업용 유료).
- 핵심 계산은 app/core.js(`judge`, `quote`, `claCheck`, `parseTiers`, `allocate`), 화면은 app/index.html + style.css. 외부 CDN·서버 호출·http 주소 금지.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 시험: `node --test tests/test_all.js`. 돈 계산은 allocate()로 항목 합 = 총합이 되게 한다.
- 법률 자문 아님 표시와 "구간·단가는 예시값" 표시를 화면에서 지우지 않는다.
- 폴더 밖 파일은 건드리지 않는다.
