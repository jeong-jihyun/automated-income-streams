# PRJ-0008 썸네일 템플릿 묶음 준비 — Claude 프로젝트 지침

## 목적
썸네일·채널아트 PNG를 점검하고 미리보기 모음, 구매자 안내 PDF, 상품 설명 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 7건 통과를 확인한다.
- Canva·Gumroad 자동 로그인·등록·입력은 만들지 않는다.
- 규격 숫자는 `config/specs.json` 예시값이라고 알리고 공식 안내 확인을 권한다.
- 안내 PDF의 "공식 상품이 아님" 문구를 지우지 않는다.

## 구조
thumb_pack/{checker,preview,guide_pdf,listing,cli,specs}.py · config/specs.json · sample/pack.json · tests/ · docs/ · claude/

## 자주 하는 요청
1. "규격 변경" → `specs.json` 의 `kinds`
2. "모음 이미지 열 수 변경" → `contact_sheet.columns`
3. "안내 PDF 문구 수정" → `guide_pdf.py`
