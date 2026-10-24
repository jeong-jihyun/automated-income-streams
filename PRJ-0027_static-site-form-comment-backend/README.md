# PRJ-0027 정적 사이트 폼·댓글 백엔드

서버가 없는 사이트(블로그 등)에 **문의 폼과 댓글**을 붙일 수 있게 해 주는 작은 API 서버입니다. 파이썬 표준 라이브러리(SQLite, http.server)만 씁니다.

- 허용한 주소(origins)에서 온 요청만 받음(`*` 모두 허용은 설정 단계에서 거부), 사람에게 안 보이는 함정 칸(`_gotcha`)이 채워지면 봇으로 보고 저장하지 않음, IP별 분당 호출 제한
- 폼: 항목별 필수·길이·이메일 형식 검사 / 댓글: 기본은 관리자 승인 후 공개
- 관리자 기능(토큰 필요): 대기 댓글 보기, 승인·거절, 폼 제출 CSV 내려받기(엑셀 수식 실행 방지 처리)

```bash
python -m form_backend check --config sample/sites.json
python -m form_backend serve --config sample/sites.json --port 8100
# 사이트에서: fetch("http://127.0.0.1:8100/f/blog/contact", {method:"POST", body: JSON.stringify({name, email, message})})
python -m pytest -q
```
API: `POST /f/<사이트>/<폼>`, `POST /c/<사이트>`, `GET /c/<사이트>?page=/경로`, `GET /admin/pending`, `POST /admin/approve|reject/<번호>`, `GET /admin/export/<사이트>/<폼>` (관리자는 `X-Admin-Token` 헤더)

## 확인한 것 / 못 한 것
- 확인(테스트 10개): 입력 검사, 허용 주소 밖 거부(403)와 CORS 응답, 함정 칸 무시, 호출 제한(IP별·1분 뒤 해제), 알림 실패해도 제출은 저장, 댓글 승인 흐름, 관리자 토큰, CSV 수식 방지, 큰 요청 거부(413), 실제 HTTP로 전체 흐름.
- **못 한 것**: HTTPS·도메인·운영 서버 배포(이 서버는 HTTPS 없이 로컬 시험용), 실제 메일 알림(notifier는 시험 출력), 캡차, 영구 백업, 구독 결제·관리자 화면은 없습니다. 댓글은 **원문 그대로** 돌려주므로 사이트에서 화면에 넣을 때 반드시 `textContent`로 넣어야 합니다(`innerHTML` 금지). 호출 제한은 서버 프로세스 메모리 기준이라 여러 서버로 늘리면 따로 셉니다. 프록시 뒤에서는 IP가 프록시 주소로 보입니다. 개인정보(이메일 등)를 저장하므로 개인정보 처리 안내와 보관 기간 정책이 필요합니다.
