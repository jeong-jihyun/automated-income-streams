# PRJ-0023 작업 규칙
- 한국어, 쉬운 말. 인식 결과는 틀릴 수 있다고 항상 안내. 한글 OCR은 kor 언어 데이터가 있어야 하며 미확인 상태를 README에 유지.
- 구조: ocr_app/engine.py(tesseract 호출) parse.py(영수증·명함 규칙) export.py(CSV) cli.py. 테스트: python -m pytest -q
