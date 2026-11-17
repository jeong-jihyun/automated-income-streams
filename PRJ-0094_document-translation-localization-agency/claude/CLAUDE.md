# CLAUDE.md
- 항목: PRJ-0094 문서 번역·현지화 자동화 대행 (업무자동화).
- 핵심 점검·계산은 app/core.js, 화면은 app/index.html + style.css. 외부 CDN·서버 호출·외부 AI 호출 금지. app 안에 'http' 글자를 쓰지 않는다(주소 정규식은 'ht'+'tp' 식으로 조립).
- 번역은 하지 않는다. 점검(빈 문단, 숫자·날짜·주소·고유명사, 용어집, 길이 비율, 문단 수)과 견적만 한다.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 시험: `node --test tests/test_all.js`. 돈 계산은 항목 합 = 총합이 되도록 allocate()로 나머지를 처리한다.
- 폴더 밖 파일은 건드리지 않는다.
