---
name: sheet-template-generator
description: 가계부·프로젝트 관리·재고 관리 구글 시트(.xlsx) 템플릿을 직무별로 만들고, 수식 오류를 검사하고, 상품 문구 초안을 만들 때 사용.
---

# 구글 시트 템플릿 생성 스킬

프로젝트 폴더: `PRJ-0002_google-sheets-template-shop/` (이 안에서 명령을 실행한다)

## 순서
1. 템플릿 종류(budget/project/inventory), 직무(freelancer/shop_owner/student), 테마(navy/sage/rose)를 확인한다.
2. `python -m engine.cli --kind <종류> --job <직무> --theme <테마> --out output` 실행.
3. 출력의 `check.ok` 가 true 인지 본다. false면 `check.static`(없는 시트·#REF!)과 `check.errors`(계산 오류값)의 셀 위치를 고친다.
4. `output/listing_*.json` 문구를 사용자에게 보여 주고 다듬는다.
5. 구글 시트 확인과 상품 등록은 사람이 한다. 전달은 "사본 만들기" 링크를 쓰도록 안내한다.

## 주의
- 재계산에는 LibreOffice가 필요하다.
- 프로젝트 템플릿의 상태(지연/대기)는 오늘 날짜(TODAY)에 따라 바뀐다.
