# PRJ-0012 영상 편집 프리셋·자막 템플릿 판매 → 자막 스타일 묶음 준비 도구 (video_preset)

스타일 설정 파일(JSON) 하나로 아래를 만들어 줍니다.

1. 설정 점검 (색 값, 글자 크기 범위, 정렬 번호, 중복 id, **설치된 글꼴인지**)
2. 자막 파일: 스타일마다 `ass/` 와 `srt/`, 전체 스타일 `all_styles.ass`
3. 미리보기: ffmpeg 로 배경 위에 자막을 입힌 3초 mp4 + GIF
4. 글꼴 라이선스 점검 목록, 구매자 안내 PDF, 판매용 ZIP, 상품 설명 초안

프리미어·캡컷 앱 조작, **전용 프리셋 파일 직접 제작**, 마켓 로그인·등록은 하지 않습니다. 앱 전용 프리셋은 구매자(또는 판매자)가 앱에서 값을 맞춰 직접 저장하도록 안내서에 순서를 적었습니다.

## 준비
Python 3.10+, `pip install -r requirements.txt`, ffmpeg (미리보기용, ass 필터 포함)

## 실행
```
python -m video_preset check --config sample/styles.json
python -m video_preset build --config sample/styles.json --out ./dist
python -m video_preset build --config my.json --out ./dist --no-preview
```
- `sample/styles.json` 형식: 스타일마다 글꼴, 크기, 색(`#RRGGBB`), 테두리, 그림자, 위치(1~9), 등장/퇴장 효과(ms), 샘플 문구
- `fonts` 목록에 글꼴의 라이선스와 받는 곳을 적으면 점검 목록에 그대로 나옵니다.
- 문제가 있으면 목록만 보여 주고 멈춥니다.

## 테스트
`python -m pytest -q` → 14건 (잘못된 색·크기·정렬·없는 글꼴·중복 id, ASS 색 변환·시간 형식, SRT 구조, 줄바꿈, 미리보기 mp4 1280x720·3초, 글꼴 점검 목록, PDF 4쪽, ZIP 안 파일, 명령 끝까지)

## 알려진 한계 (솔직하게)
- **프리미어·캡컷에서 실제로 열리고 같은 모양으로 보이는지는 확인하지 못했습니다.** ASS 는 ffmpeg(libass)로만 확인했습니다. 프리미어는 ASS 를 직접 못 열 수 있어 안내서는 SRT 사용을 권합니다.
- 안내서의 앱 메뉴 이름은 예시입니다. 버전마다 다를 수 있습니다.
- 마켓(Envato, 크몽) 승인 기준·수수료, 판매 성과는 확인하지 못했습니다.
- 글꼴 설치 여부는 `fc-list` 로 확인합니다. `fc-list` 가 없는 환경에서는 확인을 건너뛰고 경고만 냅니다.
- 이 도구는 글꼴 파일을 ZIP에 넣지 않습니다. 글꼴 재배포 가능 여부는 사람이 확인해야 합니다.
- 미리보기에 음악·효과음·영상 소스는 넣지 않습니다 (단색 배경).
