# PRJ-0005 로열티프리 BGM 구독 라이브러리 (BGM 카탈로그 도구)

곡 파일과 곡 정보 CSV가 있으면 아래를 자동으로 만들어 주는 명령줄 도구입니다.

1. 곡 정보 검증 (특히 **권리 근거**가 빠진 곡 찾기)
2. 음량을 맞춘 30초 미리듣기 mp3
3. 곡 목록 정적 사이트 (`index.html`)
4. 구독자용 라이선스 안내문 **초안** (`LICENSE_GUIDE.md`)

작곡, 결제 연결, 사이트 공개, 플랫폼 등록은 하지 않습니다. 사람이 합니다.

## 준비
- Python 3.10+, ffmpeg (ffprobe 포함)

## 실행
```
python -m bgm_catalog sample/tracks.csv ./내음악폴더 ./결과 --title "우리 BGM"
```
검증에 실패하면 문제 목록만 출력하고 파일은 만들지 않습니다.

## CSV 열
`id,title,file,mood,genre,bpm,made_by,tool,rights_basis,terms_checked`
- `made_by`가 `ai` 이면 `tool`(도구 이름)과 `terms_checked`(약관 확인일 YYYY-MM-DD)가 꼭 필요합니다.
- `sample/tracks.csv` 를 복사해서 쓰세요.

## 테스트
```
python -m pytest -q
```
합성 사인파 곡으로 검증·미리듣기 길이·사이트 곡 수·HTML 이스케이프·오류 케이스를 확인합니다 (11건).

## 확인하지 못한 것
- 실제 구독 결제, 저작권 분쟁 대응, 영상 플랫폼 Content ID
- 라이선스 안내문은 초안입니다. 공개 전 전문가 확인이 필요합니다.
- 실제 곡·실제 브라우저 재생 환경에서의 확인
