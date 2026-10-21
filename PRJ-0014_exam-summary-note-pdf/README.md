# PRJ-0014 자격증·시험 요약노트 PDF 판매

직접 쓴 요약 원고(마크다운 일부 문법)를 **목차·용어 박스·암기표·확인 문제가 있는 PDF**로 만들어 주는 명령줄 도구입니다.
인쇄용(A4)/태블릿용, 무료 맛보기 PDF, 구매자 이름 워터마크 PDF, 표지 이미지, 상품 설명 초안까지 만듭니다.
**클래스101·크몽에 자동 등록하지 않습니다.** 파일을 만들어 주기만 하고 등록은 직접 합니다.

## 설치·실행
```bash
pip install -r requirements.txt
python -m exam_note check --manuscript sample/note.md
python -m exam_note build --manuscript sample/note.md --out output --exam 정보처리기사 --preview-pages 3 --buyer 홍길동
python -m pytest -q
```
## 원고 문법
`# 제목`(1개) / `## 장` / `### 절` / 문단 / `- 목록` / 표(`|---|`) / `> 용어: 설명` / `Q: 문제` 다음 줄 `A: 정답`
형식이 틀리면 몇 행인지 알려 주고 PDF를 만들지 않습니다. "합격 보장" 같은 과장 표현도 막습니다.

## 결과물
`note_print.pdf`, `note_tablet.pdf`, `preview_free.pdf`, `note_print_<구매자>.pdf`, `cover.png`, `listing_draft.txt`

## 확인한 것 / 못 한 것
- 확인(테스트 12개, 예시 원고): 형식 오류 감지, 목차 쪽번호가 실제 PDF 위치와 일치, 맛보기 쪽수, 모든 쪽에 워터마크, 레이아웃 크기 차이, 금지 표현 차단.
- **못 한 것**: 이 환경에는 한글 PDF 뷰어 글꼴이 없어 한글이 화면에 제대로 그려지는지 눈으로 보지 못했습니다. 기본 글꼴은 파일에 넣지 않는 CID 한글 글꼴이라 뷰어(Acrobat 등)가 글자를 그립니다. 확실히 하려면 `--font 글꼴.ttf`(TrueType 한글 글꼴, 라이선스 확인)로 PDF에 글꼴을 넣으세요.
- 표지 글자는 Noto Sans CJK가 있을 때만 정상입니다. 없으면 경고가 나옵니다.
- 클래스101·크몽의 등록 규정·수수료, 내용의 정확성, 기출문제·교재 저작권은 사람이 확인해야 합니다.
- 파일 크기를 위해 쓸 수 있는 압축은 꺼 두었습니다(텍스트 위주라 크기가 작음).
