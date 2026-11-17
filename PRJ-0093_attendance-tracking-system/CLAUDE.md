# CLAUDE.md
- 항목: PRJ-0093 근태·출퇴근 자동 집계 시스템 (업무자동화).
- 핵심 계산은 app/core.js, 화면은 app/index.html + style.css. 외부 CDN·서버 호출·http 주소 금지.
- 저장은 localStorage(try/catch)만. 결제·전송·로그인 없음.
- 기준값(소정 8시간, 야간 22~06시, 휴게, 가산, 시급)은 예시이며 화면 입력칸에서 바꾼다. 세법·노동법 자문 아님을 화면에 유지한다.
- 시험: `node --test tests/test_all.js`. 급여 참고는 전체를 한 번 반올림한 뒤 allocate()로 직원별로 나눠 직원 합 = 총액이 되게 한다.
- 폴더 밖 파일은 건드리지 않는다.
