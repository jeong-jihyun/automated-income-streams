# PRJ-0008 유튜브 썸네일·채널아트 템플릿 판매 → 템플릿 묶음 준비 도구 (thumb_pack)

Canva에서 디자인한 PNG/JPG 미리보기를 점검하고, **판매용 미리보기 모음 이미지, 구매자 안내 PDF(템플릿 링크 포함), 상품 설명 초안**을 만들어 줍니다.
템플릿 디자인, Canva·Gumroad 로그인·자동 등록, 가격 결정은 하지 않습니다.

## 준비
Python 3.10+, `pip install -r requirements.txt`

## 실행
```
python -m thumb_pack check --input ./png
python -m thumb_pack build --input ./png --config sample/pack.json --out ./dist
```
- 파일 이름 규칙: `thumb_이름-01.png` (1280x720, 2MB 이하), `art_이름-01.png` (2560x1440, 6MB 이하) — 영문 소문자·숫자·하이픈
- `sample/pack.json` 에 묶음 이름, 테마, 템플릿 링크, 글꼴 이름을 적습니다 (샘플 링크는 가짜입니다).
- 불합격이 있으면 목록만 보여 주고 멈춥니다.
- 안내 PDF에는 "유튜브·구글 공식 상품이 아님" 문구가 들어갑니다.

## 규격 설정 (중요)
`config/specs.json` 의 크기·용량은 **예시값**입니다. 공식 안내를 확인하고 고치세요.

## 테스트
`python -m pytest -q` → 7건 (더미 이미지 8장: 정상 4, 크기 틀림 2, 용량 큼 1, 파일명 문제 1 / 모음 이미지 칸 수 / PDF 쪽수·링크 / 오류 케이스 / 명령 끝까지)

## 알려진 한계
- Canva·Gumroad 실제 화면과 규정, 실제 판매 성과는 확인하지 못했습니다.
- 안내 PDF는 기본 한글 글꼴(CID)을 써서 PDF 보기 프로그램에 따라 글꼴 모양이 다를 수 있습니다.
- Canva 템플릿 판매 규정(소재 재판매 제한 등)은 판매 전에 사람이 확인해야 합니다. 상품 설명 초안에 확인 항목을 넣어 두었습니다.
