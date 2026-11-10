import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="kgoods", description="굿즈 해외 배송 견적·제한 점검")
    p.add_argument("orders"); p.add_argument("--rates", required=True); p.add_argument("--rules", required=True)
    p.add_argument("--krw-per-usd", type=float, default=1400.0)
    a = p.parse_args(argv)
    try:
        if a.krw_per_usd <= 0: raise ValueError("환율은 0보다 커야 합니다")
        rates = json.load(open(a.rates, encoding="utf-8")); rules = json.load(open(a.rules, encoding="utf-8"))
        qs = [core.quote(o, rates, rules, a.krw_per_usd) for o in core.read_orders(a.orders)]
    except (OSError, ValueError, KeyError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.report(qs)); return 0
