# PRJ-0012 자막 스타일 묶음 준비 — Claude 프로젝트 지침

## 목적
스타일 설정 JSON으로 ASS/SRT, 미리보기, 글꼴 라이선스 목록, 안내 PDF, ZIP, 설명 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 14건 통과를 확인한다.
- 마켓 자동 등록·입력, 앱 전용 프리셋 파일 직접 제작은 하지 않는다.
- 프리미어·캡컷에서 실제로 열리는지는 확인하지 못했다고 항상 알린다.
- 글꼴 파일을 ZIP에 넣지 않는다. 라이선스는 사람이 확인하게 안내한다.

## 구조
video_preset/{config,subs,preview,package,cli}.py · sample/styles.json · tests/ · docs/ · claude/

## 자주 하는 요청
1. "스타일 항목 추가" → `config.LIMITS`, `subs.style_line`
2. "미리보기 길이 변경" → `preview.make_preview(seconds=)`
3. "안내서 문구 수정" → `package.guide_pdf`
