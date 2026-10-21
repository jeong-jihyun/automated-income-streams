# PRJ-0020 국내 커머스 API 통합 중개 (게이트웨이 뼈대)

네이버·쿠팡·카카오 주문 응답을 **하나의 공통 주문 형식**으로 묶어 주는 게이트웨이의 뼈대입니다. API 키 확인, 분당 호출 제한, 사용량(과금용) 집계, 30초 캐시, 한 채널이 실패해도 나머지 반환을 포함합니다.

```bash
python -m kr_gateway check --mappings sample/mappings.json --keys sample/keys.json
python -m kr_gateway serve --mappings sample/mappings.json --keys sample/keys.json --port 8090
curl -H "X-API-Key: demo-key-123" "http://127.0.0.1:8090/v1/orders?channel=naver,kakao"
python -m pytest -q
```
채널별 필드 이름은 `sample/mappings.json`에서 바꿉니다(코드를 고치지 않아도 됨).

## 꼭 읽어 주세요 (못 한 것)
- **실제 네이버·쿠팡·카카오 API에는 연결하지 않았습니다.** 인증(OAuth·서명), 실제 응답 형식, 호출 한도는 확인하지 못했습니다. `mappings.json`의 필드 이름은 **추정한 예시값**이며 실제 API 문서로 확인·수정해야 합니다. 서버(`serve`)는 가짜 응답으로만 동작합니다.
- 실제 연동 시 필요한 것: 각 플랫폼 판매자/개발자 등록과 API 이용 약관 확인, 인증 구현(채널별 `fetcher` 함수 작성), 비밀키 보관.
- 과금·결제, 키 발급 화면, 영구 저장(재시작하면 사용량·캐시가 사라짐), RapidAPI 등록은 없습니다.
- 확인한 것(테스트 9개): 공통 형식 변환·최신순 정렬, 모르는 상태 → unknown, 필드 빠진 행 건너뛰기와 개수 보고, 응답 형식 변경 감지, 키 확인·분당 한도(1분 뒤 해제), 캐시, 부분 실패, 전체 실패 시 사용량 미차감, 매핑 검증, 실제 HTTP 호출.
