# 설계 요약
- extract: ast(파이썬)/json(OpenAPI) → 항목. translate: 원문 해시 → {src, ko, status}. render: 항목+번역 → 마크다운. cli: build.
- 설계 문서(드라이브)는 읽지 않고 시트 한 줄 설명으로 범위를 잡았다.
- 범위 밖: 유료 번역 API 연동, 호스팅, 마켓플레이스 등록.
