# PRJ-0007 AI 컬러링북 출판 → 컬러링북 제작 보조 도구 (coloring_book)

흑백 선화 그림 폴더로 KDP용 **내지 PDF, 표지 PDF(가이드선 포함), 제목·설명·키워드 초안**을 만들어 줍니다.
그림 만들기(AI 도구 실행), KDP 로그인·자동 업로드·가격 결정은 하지 않습니다. 사람이 직접 합니다.

## 준비
Python 3.10+, `pip install -r requirements.txt` (Pillow, reportlab, pypdf)

## 실행
```
python -m coloring_book check --input ./images --trim 8.5x11
python -m coloring_book build --input ./images --trim 8.5x11 --out ./book --theme 고양이 --paper white
```
1. 이미지를 점검합니다 (크기, 흰 배경, 색 섞임, 회색 면). 불합격이 있으면 목록만 보여 주고 멈춥니다.
2. 내지 PDF: 그림 한 장 + 뒷면 빈 페이지(끄려면 `--no-blank-back`), 최소 쪽수·짝수 쪽수로 맞춤
3. 표지 PDF: 쪽수에 따라 책등 두께를 계산해 크기를 정하고, 접는 선 가이드를 그림 (업로드 전에 지울 것)
4. `metadata_draft.txt`: 제목·설명·키워드 초안과 AI 사용 여부 안내

## 규격 설정 (중요)
`config/kdp_specs.json` 의 책 크기, 블리드, 종이 두께, 최소/최대 쪽수는 **예시값**입니다. KDP 공식 안내를 확인하고 고치세요.

## 테스트
`python -m pytest -q` → 9건 (더미 선화: 정상 6, 너무 작음, 회색 배경, 회색 면, 색 섞임, 텍스트 파일 무시, 깨진 파일, 쪽수·크기, 책등 계산, 명령 끝까지)

## 알려진 한계
- 실제 KDP 규격 숫자, KDP 미리보기 통과, 인쇄 품질은 확인하지 못했습니다.
- 선 굵기 검사는 만들지 않았습니다 (크기·배경·색·회색 면만 검사).
- 블리드 옵션은 단순 계산이라 KDP 템플릿과 다를 수 있습니다.
- 표지 PDF는 가이드 틀이며 디자인 완성본이 아닙니다.
