# PRJ-0001 굿노트 디지털 플래너 — Claude 프로젝트 지침

## 목적
하이퍼링크 플래너 PDF를 자동 생성하고, 판매 상품 등록에 쓸 이미지·문구 초안을 만든다.

## 작업 규칙
- 답변은 한국어로, 쉬운 말로, 생각의 흐름이 보이게 설명한다.
- 코드를 바꾸면 `python -m pytest -q` 를 먼저 돌려 통과를 확인한다.
- 링크 검증은 `engine/validate.py` 의 `link_targets` 로 출발·도착 페이지를 비교한다.
- 플랫폼(Etsy 등) 상품 등록은 자동화하지 않는다. 문구·이미지 초안까지만 만든다.
- 폰트는 상업 이용 가능한 것만 쓴다(NanumGothic OFL 내장).

## 폴더
engine/(Python) · ui/(React) · desktop/(Electron) · docs/ · claude/

## 자주 하는 요청
1. "2028년 일요일 시작 영문 플래너 만들어줘" → `python -m engine.cli --year 2028 --week-start sunday --lang en`
2. "테마 추가" → `engine/config.py` 의 THEMES 에 항목 추가, 테스트 확인
3. "상품 문구 수정" → `engine/copy_text.py`
