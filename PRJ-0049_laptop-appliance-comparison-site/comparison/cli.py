import argparse
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="comparison", description="스펙 비교표와 가격 기록 (입력 자료만 사용)")
    s = p.add_subparsers(dest="cmd", required=True)
    b = s.add_parser("build"); b.add_argument("products"); b.add_argument("--history", default="prices.csv"); b.add_argument("--out", default="compare.html"); b.add_argument("--today")
    a_ = s.add_parser("add-price"); a_.add_argument("id"); a_.add_argument("price", type=int); a_.add_argument("--history", default="prices.csv"); a_.add_argument("--date")
    a = p.parse_args(argv)
    try:
        if a.cmd == "add-price":
            core.add_price(a.history, a.id, date.fromisoformat(a.date) if a.date else date.today(), a.price); print("기록했어요"); return 0
        today = date.fromisoformat(a.today) if a.today else date.today()
        open(a.out, "w", encoding="utf-8").write(core.render(core.load_products(a.products), core.load_history(a.history), today)); print(f"만들었어요: {a.out}"); return 0
    except (core.CompareError, ValueError) as e:
        print(f"[오류] {e}"); return 2
