# PRJ-0006 스톡 업로드 준비 도구 — Claude 프로젝트 지침

## 목적
스톡 사진 업로드 전 파일 검사, 키워드 정리, 메타데이터 CSV, 릴리스 체크리스트를 만든다.

## 작업 규칙
- 답변은 한국어로, 쉬운 말로, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 로 10건이 모두 통과하는지 확인한다.
- 자동 로그인·자동 업로드·자동 입력, 이미지 외부 전송 기능은 만들지 않는다.
- 규격 숫자와 CSV 열 이름은 `stock_prep/settings.json` 의 예시값이라고 항상 알리고 공식 안내 확인을 권한다.
- 사람·상표·건물 내부 판단은 경고만 하고 최종 판단은 사람이 한다.

## 구조
stock_prep/core.py(검사·키워드·CSV·보고서) · cli.py · settings.json · tests/ · sample/memo.csv · docs/ · claude/

## 자주 하는 요청
1. "사이트 추가" → `settings.json` 의 `sites` 에 열 이름 추가 후 테스트
2. "금지어 추가" → `keywords.banned`
3. "해상도 기준 변경" → `check.min_megapixels`
