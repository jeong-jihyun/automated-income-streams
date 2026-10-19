---
name: goodnotes-planner-generator
description: 하이퍼링크가 걸린 굿노트용 연간·월간·주간·일간 플래너 PDF를 만들고, 링크를 검증하고, 상품 등록용 이미지·문구 초안을 만들 때 사용.
---

# 굿노트 플래너 생성 스킬

프로젝트 폴더: `PRJ-0001_goodnotes-digital-planner/` (이 안에서 명령을 실행한다)

## 순서
1. 사용자에게 연도, 주 시작 요일(monday/sunday), 언어(ko/en), 테마(navy/sage/rose/mono)를 확인한다.
2. `python -m engine.cli --year <연도> --week-start <요일> --lang <언어> --theme <테마> --out output` 실행.
3. 출력의 `check.ok` 가 true 인지 확인한다. false면 `check.broken` 의 출발 페이지를 보고 원인을 고친다.
4. `output/previews/` 이미지와 `output/listing_copy.json` 을 사용자에게 전달한다.
5. 굿노트에서 링크 클릭 확인과 플랫폼 등록은 사람이 한다고 안내한다.

## 주의
- 한글이 비어 보이면 폰트가 내장되지 않은 것이다. `engine/fonts/NanumGothic.ttf` 존재를 확인한다(폰트 넣는 방법: `engine/fonts/FONT_README.md`).
- 일간 페이지를 켜면 약 440페이지, 2MB 안팎이다.
