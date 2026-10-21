# PRJ-0014 작업 규칙
- 한국어, 쉬운 말. 기출문제·교재 복사 금지, 시험 기관 로고·상표 금지, "합격 보장" 류 표현 금지.
- 플랫폼 자동 등록/업로드 기능을 만들지 않는다. 미확인 항목(한글 렌더링, 플랫폼 규정)은 정직하게 적는다.
- 구조: exam_note/parser.py(원고 점검) pdfgen.py(PDF·목차) outputs.py(맛보기·워터마크·표지·설명) cli.py
- 목차는 multiBuild + beforeDocument에서 headings 초기화(안 하면 수렴 실패). 테스트: python -m pytest -q
