# PRJ-0010 회화 오디오북 제작 보조 — Claude 프로젝트 지침

## 목적
문장표 CSV로 챕터 mp3, 목차, 교재 PDF, 상품 설명 초안을 만든다.

## 작업 규칙
- 한국어, 쉬운 말, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 9건 통과를 확인한다.
- 마켓 자동 등록은 만들지 않는다. 다른 교재의 문장을 옮기지 않는다.
- `silent` 는 시험용이고 `edge-tts` 는 약관 위험이 있음을 항상 알린다.
- 발음·번역 품질은 확인할 수 없다고 알린다.

## 구조
audiobook_builder/{sheet,tts,audio,textbook,listing,cli}.py · config/settings.json · sample/sentences.csv · tests/ · docs/ · claude/

## 자주 하는 요청
1. "간격 변경" → `--gap` 또는 `gap_sec`
2. "새 음성 제공자" → `tts.py` 에 클래스 추가 후 `PROVIDERS` 등록
3. "PDF 글꼴 변경" → `pdf_font`
