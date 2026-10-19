# PRJ-0001 굿노트 디지털 플래너 생성기

연도·시작 요일·언어·색상을 고르면 **하이퍼링크가 걸린 플래너 PDF**를 자동으로 만들어 주는 프로그램입니다.
오른쪽 탭(연간, 1~12월, 노트), 연간 달력의 월·날짜, 월간 달력의 날짜가 눌러서 이동됩니다.

## 맡는 범위
- 자동화: PDF 생성, 링크 연결, 링크 검증, 미리보기 이미지, 상품 문구 초안
- 사람이 하는 일: 굿노트에서 최종 확인, Etsy·아이디어스·스마트스토어 등록, 가격·응대

## 빠른 시작
```bash
pip install -r requirements.txt
python -m engine.cli --year 2027 --lang ko --theme navy --out output
python -m pytest -q   # 테스트
```
결과: `output/planner_2027_ko_navy.pdf`, `output/previews/*.png`, `output/listing_copy.json`

## 화면(React) + PC 프로그램(Electron)
```bash
cd ui && npm install && npm run build
cd ../desktop && npm install && npm start
```
Electron은 Python 3가 설치된 PC에서 엔진을 호출합니다.

## 폴더
| 폴더 | 내용 |
|---|---|
| engine/ | Python 엔진 (설정 검증, 달력 계산, PDF 생성, 링크 검증, 문구) |
| ui/ | React 설정 화면 |
| desktop/ | Electron 포장 |
| claude/ | Claude 프로젝트 지침과 스킬 파일 |
| docs/ | 분석·설계 문서 링크 |

## 폰트·저작권
NanumGothic(OFL)을 PDF에 내장합니다. 상업 판매 가능하지만 폰트 파일 단독 판매는 금지입니다. (`engine/fonts/LICENSE-NanumGothic.txt`)
다른 폰트를 쓰려면 `--font 경로.ttf` 를 지정하세요.
※ 이 저장소에는 폰트 파일(NanumGothic.ttf, 4.6MB)이 없습니다. `engine/fonts/FONT_README.md` 를 보고 넣어 주세요. 폰트가 없으면 한글이 PDF에 나오지 않습니다.

## 테스트 현황
- 엔진 15개 테스트 통과 (윤년, 2026~2030 모든 월 달력, 주 시작 요일, 링크 출발·도착 쌍 전체 비교, 깨진 링크 탐지). 2026-10-20 이 저장소에서 다시 실행해 확인했습니다. 단, 폰트 파일이 없는 상태라 한글 글자 표시는 확인하지 못했습니다.
- React 화면 빌드는 이전에 확인했습니다. 이 저장소에서는 다시 실행하지 않았습니다.
- 굿노트 앱 실제 링크 동작과 Electron 창 실행은 사람이 확인 필요
