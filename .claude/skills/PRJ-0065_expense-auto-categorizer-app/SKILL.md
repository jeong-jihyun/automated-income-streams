---
name: expense-auto-categorizer-app
description: 붙여넣은 카드 승인·취소 문자를 읽어 지출을 분류하고 월간 리포트·CSV를 만드는 도구(문자함 접근 없음, 카드번호·이름 미보관). 사용자가 가계부 자동 분류 앱 개발을 요청할 때 사용.
---
# PRJ-0065 가계부 자동 분류·월간 리포트 앱 (카드 문자 분류 도구)
`python -m expensecat <문자.txt> --rules <규칙.json> [--mine 내규칙.json] [--month YYYY-MM] [--out out.csv] | --learn 가맹점 분류`. 한계는 README 참고.
