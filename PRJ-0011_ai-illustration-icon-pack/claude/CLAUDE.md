# PRJ-0011 아이콘 팩 준비 — Claude 프로젝트 지침

## 목적
아이콘 PNG 폴더를 점검하고 크기 변환, 미리보기 모음, ZIP, 사용 안내 PDF, 상품 설명 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 7건 통과를 확인한다. 정상 세트에서 오탐이 없는 테스트도 꼭 유지한다.
- 마켓 자동 등록·입력은 만들지 않는다.
- 규격과 기준값은 `config/specs.json` 예시값이라고 알리고, 마켓 규정·AI 약관은 사람이 확인하게 안내한다.
- 디자인 품질은 판단할 수 없다고 알린다.

## 구조
icon_pack/{checker,package,cli,specs}.py · config/specs.json · tests/ · docs/ · claude/

## 자주 하는 요청
1. "크기 추가" → `specs.json` 의 `sizes`
2. "스타일 검사 완화" → `style_min_coverage`, `style_min_share`
3. "중복 판정 변경" → `duplicate_hash_distance`
