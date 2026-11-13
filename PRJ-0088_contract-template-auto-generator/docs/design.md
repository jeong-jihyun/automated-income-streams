# 설계

## 구조
- `app/core.js`: 순수 함수 모음. 브라우저에서는 `window.Core`, Node에서는 `module.exports`.
- `app/index.html` + `style.css`: 입력 폼, 점검 결과, 한글 금액, 문서 초안, 복사 버튼. 큰 글씨(기본 18px), 세로 화면 viewport.
- `tests/test_all.js`: node:test 18개.

## 흐름
템플릿 선택 → 칸 입력(자동 localStorage 저장) → `Core.build(id, values)` → `{text, check{missing,errors,warnings,ok}, hangul, disclaimer}` 표시.

## 템플릿 구조
`{id, name, fields[], body, rules(v, add)}`
- 칸 종류: text, textarea, money, number, date. `required`, `allowZero`, `min/max`, `hangulOf`(직접 쓴 한글 금액을 숫자 칸과 대조).
- 본문의 `{{칸}}`은 값으로, `{{금액칸_한글}}`은 자동 한글 금액으로 바뀜. 금액은 쉼표, 날짜는 'YYYY년 M월 D일'로 표시. 필수 칸이 비면 【라벨 입력 필요】.

## 판정 규칙
- 금액: 숫자만(쉼표·원 허용), 0 불가 칸 구분, 최대 9,999,999,999,999,999.
- 한글 금액: 1을 생략하지 않는 계약서식(일십, 일만). 직접 쓴 값은 '일금'·'원'·'정'·공백을 빼고 비교하며 1 생략 표기(만, 백)도 허용.
- 용역: 계약금+중도금+잔금 = 총액(아니면 오류와 차액), 계약일 ≤ 시작일 ≤ 종료일, 잔금일 ≥ 계약일(종료일보다 빠르면 경고).
- 임대차: 계약일 ≤ 시작일 < 종료일, 월세일 1~31, 월세 0원은 경고.
- 차용증: 차용일 ≤ 변제일, 이자율 0~100, 20% 초과 경고(예시 기준).
- 자동 나누기 `splitPayment`: 마지막 칸이 나머지를 받아 합계가 항상 총액과 같음.

## 한계
- 법률 자문이 아니며 조항 문구는 예시. 실제 사용 전 전문가 확인 필요.
- 실제 폰·브라우저 화면은 확인하지 못함.
