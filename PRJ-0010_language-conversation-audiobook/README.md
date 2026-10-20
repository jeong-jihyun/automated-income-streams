# PRJ-0010 외국어 회화 오디오북 교재 판매 → 회화 오디오북 제작 보조 도구 (audiobook_builder)

문장표 CSV 한 장으로 아래를 만들어 줍니다.

1. 문장표 점검 (빈 칸, 번호·문장 중복, 너무 긴 문장)
2. 문장별 음성 + 따라 말하기 무음 간격(기본 3초) → 상황(챕터)별 mp3
3. 목차 `toc.txt` (챕터·문장 시작 시각)
4. 교재 PDF (문장·뜻·발음)
5. 상품 설명·목차 초안

번역·문장 고르기는 사람이 합니다. 윌라·크몽 등록은 하지 않습니다.

## 준비
Python 3.10+, ffmpeg, `pip install -r requirements.txt`

## 실행
```
python -m audiobook_builder check --sheet sample/sentences.csv
python -m audiobook_builder build --sheet sample/sentences.csv --out ./book --provider silent --gap 3
python -m audiobook_builder build --sheet 문장표.csv --out ./book --provider folder --recordings ./내녹음
```
- 문장표 열: `no, situation, text, meaning, pronunciation(선택)` — 쉼표가 들어간 문장은 큰따옴표로 감싸세요.
- 음성 제공자(교체 가능):
  - `silent`: **시험용 무음** (글자 수에 비례한 길이). 판매용이 아닙니다.
  - `folder`: 직접 녹음한 파일 사용 (`1.wav`, `2.mp3` …, 번호와 같은 이름)
  - `edge-tts`: 선택 설치. **비공식 도구라 상업 이용·재판매 약관 위험이 있습니다.** 판매 전에 공식 약관 확인 필수.

## 테스트
`python -m pytest -q` → 9건 (CSV 점검, 챕터 길이·간격 계산 ±0.02초, 시작 시각, 녹음 폴더 변환, 오류 케이스, PDF 쪽수, 명령 끝까지). 음성 생성부는 가짜(무음)로 대체해서 확인했습니다.

## 알려진 한계 (솔직하게)
- 실제 발음 품질, 번역 정확성, 마켓 심사는 확인하지 못했습니다.
- `edge-tts` 는 이 환경에서 네트워크로 실행해 보지 못했습니다 (코드만 있고 시험하지 않음).
- 교재 PDF 글꼴은 기본 한글(CID) 글꼴입니다. 일본어·중국어 문장은 `config/settings.json` 의 `pdf_font` 를 바꿔야 하고 (예: HeiseiMin-W3, STSong-Light) 그 경우도 시험하지 않았습니다.
- mp3 길이는 인코딩 때문에 계산값과 0.3초 안쪽으로 다를 수 있습니다.
