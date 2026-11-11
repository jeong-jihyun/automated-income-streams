---
name: small-invest-strategy-backtester
description: 가격 CSV로 존버·적립식·이동평균 전략을 비용 반영해 백테스트하고 MDD·연환산 수익률을 비교하는 도구(투자 조언 아님, 가격 수집 없음). 사용자가 소액 투자 백테스트 서비스 개발을 요청할 때 사용.
---
# PRJ-0069 소액 투자 전략 백테스트 서비스 (단순 전략 비교 도구)
`python -m backtest <prices.csv> [--cash N] [--monthly N] [--fee R] [--slip R] [--fast N] [--slow N]`. 한계는 README 참고.
