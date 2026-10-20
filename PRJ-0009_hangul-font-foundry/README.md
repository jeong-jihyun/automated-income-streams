# PRJ-0009 한글 폰트 제작·판매 → 한글 폰트 제작 보조 도구 (hangul_font_kit)

글자를 그리는 일(디자인)은 사람이 합니다. 이 도구는 힘든 반복 작업을 맡습니다.

1. `charset`: 필수 글자 목록 만들기 (KS X 1001 완성형 한글 2,350자 + 숫자·영문·기본 기호)
2. `check`: 빠진 글자, 파일명 규칙(`U+AC00.svg`), 캔버스(1000x1000) 이탈, 열린 경로, 지원하지 않는 명령 찾기
3. `build`: SVG → TTF 만들기 + 글자 견본표 PNG, 문장 미리보기, 견본 PDF, 라이선스·상품 설명 초안

마켓 입점·심사·등록은 하지 않습니다. 사람이 직접 합니다.

## 준비
Python 3.10+, `pip install -r requirements.txt` (fontTools, Pillow, reportlab, pypdf)

## 실행
```
python -m hangul_font_kit charset --out chars.csv
python -m hangul_font_kit check --glyphs ./glyphs
python -m hangul_font_kit build --glyphs ./glyphs --out ./font_out
```
- 글리프 파일: `glyphs/U+AC00.svg` (viewBox `0 0 1000 1000`, 기준선은 위에서 800). `<path>` 는 **절대좌표 M L H V C Q Z** 와 `<rect>` 만 지원합니다.
- 빠진 글자가 있으면 `build` 가 멈춥니다. 시험용으로 만들려면 `--allow-missing`.
- 설정(글꼴 이름, 자간, 미리보기 문장)은 `config/font.json`.

## 테스트
`python -m pytest -q` → 10건 (글자 수 2,350, 파일명·이탈·열린 경로·상대좌표·깨진 SVG 검출, 곡선 처리, 샘플 글자 20자로 TTF를 만들고 다시 읽어 확인, 견본·PDF, 명령 끝까지)

## 알려진 한계 (솔직하게)
- 만든 글리프는 단순 사각형·곡선 시험용입니다. 실제 글자 디자인 품질은 확인할 수 없습니다.
- TTF만 만듭니다. OTF(CFF)는 만들지 않습니다. 힌팅·커닝·글자 겹침 정리는 없습니다.
- 윈도우/맥 화면 표시, 마켓 심사 기준과 최소 글자 수는 확인하지 못했습니다. 입점할 마켓의 공식 안내를 확인하세요.
- SVG의 변환(transform), 상대좌표, 호(A) 명령은 지원하지 않습니다 (점검기가 알려 줍니다).
- 다른 폰트의 윤곽을 따라 그리거나 변환하지 마세요. 오픈 라이선스 폰트를 바탕으로 쓰면 그 조건(이름 변경 등)을 따라야 합니다.
- 라이선스 표는 초안입니다. 공개 전 전문가 확인이 필요합니다.
