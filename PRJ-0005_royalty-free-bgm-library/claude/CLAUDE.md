# PRJ-0005 BGM 카탈로그 도구 — Claude 프로젝트 지침

## 목적
곡 정보 CSV와 음악 파일로 미리듣기, 카탈로그 사이트, 라이선스 안내문 초안을 만든다.

## 작업 규칙
- 답변은 한국어로, 쉬운 말로, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 로 11건이 모두 통과하는지 확인한다.
- 권리 근거·AI 도구·약관 확인일 검증을 약하게 바꾸지 않는다. 이 도구의 핵심 안전장치다.
- 외부 사이트 자동 등록, Content ID 등록, 결제 직접 구현은 만들지 않는다.
- 라이선스 문구는 초안이라고 항상 알린다.

## 구조
bgm_catalog/core.py(검증·미리듣기·사이트·안내문) · cli.py · tests/ · sample/tracks.csv · docs/ · claude/

## 자주 하는 요청
1. "열 추가" → `core.REQUIRED` 와 `validate` 수정 후 테스트
2. "미리듣기 길이 변경" → `--seconds` 옵션
3. "사이트 디자인" → `build_site` 의 HTML/CSS
