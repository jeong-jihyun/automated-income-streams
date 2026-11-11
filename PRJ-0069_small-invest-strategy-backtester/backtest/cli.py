import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="backtest", description="단순 전략 백테스트")
    p.add_argument("prices"); p.add_argument("--cash", type=float, default=10_000_000); p.add_argument("--monthly", type=float, default=0)
    p.add_argument("--fee", type=float, default=0.00015); p.add_argument("--slip", type=float, default=0.0005)
    p.add_argument("--fast", type=int, default=20); p.add_argument("--slow", type=int, default=60)
    a = p.parse_args(argv)
    try:
        rows = core.load(a.prices)
        res = core.compare(rows, cash=a.cash, fee=a.fee, slip=a.slip, monthly=a.monthly, fast=a.fast, slow=a.slow)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(res, core.warnings(rows))); return 0
