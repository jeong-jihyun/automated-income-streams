# CLAUDE.md
- 항목: PRJ-0096 개발 SDK·라이브러리 라이선스 (키 검사·견적·갱신 일정).
- 핵심 계산은 app/core.js, 화면은 app/index.html + style.css. 외부 CDN·서버 호출·http 주소 금지.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 날짜는 입력칸 '오늘' 값만 쓴다. 기기 시계 호출 금지(시험이 흔들림).
- 시험: `node --test tests/test_all.js`. 돈 계산은 항목 합 = 총합이 되도록 allocate()로 나머지를 처리한다.
- 검사값은 단순 합계 규칙이며 암호 보안이 아님을 화면·문서에서 유지한다. 단가는 예시, 법률 자문 아님.
- 폴더 밖 파일은 건드리지 않는다.
