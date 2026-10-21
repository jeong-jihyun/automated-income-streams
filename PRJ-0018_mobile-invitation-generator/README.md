# PRJ-0018 모바일 청첩장·초대장 만들기

행사 정보 JSON + 사진 → **휴대폰용 초대장 HTML 한 파일**(사진은 줄여서 파일 안에 포함) + **캘린더 파일(.ics)** 을 만듭니다. D-day, 네이버 지도 링크, 전화 버튼 포함. 테마 3가지(rose/mint/navy).

```bash
pip install -r requirements.txt
python -m invitation check --config sample/event.json
python -m invitation build --config sample/event.json --out output
python -m pytest -q
```
## 확인한 것 / 못 한 것
- 확인(테스트 13개): 날짜·시간·전화번호·테마·사진 수 검증, 사진 축소(최대 900px), D-day 계산, HTML 이스케이프, .ics 형식(쉼표·세미콜론 이스케이프), 오류 안내.
- **못 한 것**: 웹에 올리는 호스팅, 카카오톡 공유 미리보기(og:image 없음), 참석 확인(RSVP)·방명록·계좌 안내는 없음(서버가 필요). 실제 휴대폰·카카오톡 인앱 브라우저에서의 모양, 달력 앱에서 .ics 열기는 확인하지 못했습니다. 사진이 많으면 HTML이 커집니다(사진당 수십~수백 KB). 건당 결제·주문 흐름은 만들지 않았습니다.
