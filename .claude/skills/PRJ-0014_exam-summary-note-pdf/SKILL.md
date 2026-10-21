---
name: exam-summary-note-pdf
description: 요약 원고(.md)를 점검하고 목차·용어 박스·암기표·확인 문제가 있는 인쇄용/태블릿용 PDF, 맛보기, 구매자 워터마크 PDF, 표지, 상품 설명 초안을 만드는 명령줄 도구. 사용자가 시험 요약노트 PDF 판매 준비를 요청할 때 사용.
---
# 사용법
1. `python -m exam_note check --manuscript 원고.md` 로 형식·금지 표현 점검
2. `python -m exam_note build --manuscript 원고.md --out output --exam 시험이름 --preview-pages 5 --buyer 이름`
3. 결과물 확인 후 플랫폼 등록은 사용자가 직접. 한글 글꼴 포함이 필요하면 `--font`.
