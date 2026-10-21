# PRJ-0013 스티커·배경화면 묶음 준비 — Claude 프로젝트 지침

## 목적
스티커 PNG와 배경화면 원본으로 가공된 스티커, 시트, 배경화면, 미리보기, 안내 PDF, ZIP, 설명 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 10건 통과를 확인한다. 시트 "겹침 없음·범위 안" 테스트는 꼭 유지한다.
- 판매 플랫폼 자동 등록·입력은 만들지 않는다.
- 굿노트·실제 폰 표시, 플랫폼 심사는 확인하지 못했다고 항상 알린다. 크기 숫자는 예시값이다.
- 캐릭터·브랜드·유명 그림체 도용 금지를 안내한다.

## 구조
sticker_shop/{checker,process,package,cli,specs}.py · config/specs.json · tests/ · docs/ · claude/

## 자주 하는 요청
1. "배경화면 크기 추가" → `specs.json` 의 `wallpaper.sizes`
2. "테두리 두께" → `sticker.border_px`
3. "시트 크기 변경" → `sheet.size`
