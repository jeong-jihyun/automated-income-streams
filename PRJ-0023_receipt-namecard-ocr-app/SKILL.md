---
name: receipt-namecard-ocr-app
description: 영수증·명함 사진(또는 OCR 글자)에서 항목을 뽑아 CSV로 정리하는 명령줄 도구(tesseract 사용, 경고·수식 방지 포함). 사용자가 영수증·명함 OCR 앱 개발을 요청할 때 사용.
---
`python -m ocr_app receipt|namecard 파일... --out 결과.csv`. 한글은 tesseract kor 데이터 필요, 결과는 사람이 확인.
