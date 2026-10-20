# PRJ-0007 컬러링북 제작 보조 — Claude 프로젝트 지침

## 목적
선화 이미지 폴더로 KDP용 내지 PDF, 표지 PDF, 메타데이터 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 9건 통과를 확인한다.
- KDP 자동 로그인·업로드·입력은 만들지 않는다. 텍스트 초안까지만.
- 규격 숫자는 `config/kdp_specs.json` 의 예시값이라고 알리고 공식 안내 확인을 권한다.
- AI 사용 여부 선택은 사람이 직접 한다고 항상 안내한다.

## 구조
coloring_book/{checker,interior,cover,metadata,cli,specs}.py · config/kdp_specs.json · tests/ · docs/ · claude/

## 자주 하는 요청
1. "책 크기 추가" → `kdp_specs.json` 의 `trim_sizes_in`
2. "책등 두께 수정" → `paper_thickness_in_per_page`
3. "검사 기준 변경" → `white_background_min_mean`, `gray_pixel_max_ratio`
