# PRJ-0017 링크 단축·클릭 분석

긴 주소를 짧은 코드로 줄이고, 누가 어디서(네이버·구글·직접…) 어떤 기기로 눌렀는지 세어 주는 **시험용 로컬 도구**입니다. 파이썬 표준 라이브러리(SQLite)만 씁니다.

## 실행
```bash
python -m link_short add https://example.com/page --code hello
python -m link_short serve --port 8080      # http://127.0.0.1:8080/hello 로 접속하면 이동 + 클릭 기록
python -m link_short stats hello             # 날짜별·유입 경로·기기·utm_source
python -m pytest -q
```
API: `POST /api/links {url, code?}`, `GET /<코드>`(302 이동), `GET /api/stats/<코드>`

## 안전 장치
http/https만 허용, `javascript:`·사설 IP·localhost 거부, 2048자 제한, 코드 중복 거부. 봇은 통계에서 기본 제외.

## 확인한 것 / 못 한 것
- 확인(테스트 14개): 나쁜 주소 9종 거부, 코드 생성·중복, 유입·기기 분류, 날짜별 집계, 봇 제외, 실제 서버에서 302 이동과 통계 API.
- **못 한 것**: 대시보드 화면(웹 UI), 로그인·구독 결제, 도메인·HTTPS 운영은 없음. 인터넷에 열면 악용(스팸·피싱 링크) 위험이 있어 별도 보안 설계(신고, 차단 목록, 요청 제한)가 필요합니다. 유입 경로 분류는 단순 도메인 비교이고, 수천 건 이상의 부하 시험은 하지 않았습니다.
