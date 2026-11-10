import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="divcal", description="배당 캘린더·알림 글 만들기")
    p.add_argument("holdings"); p.add_argument("schedule"); p.add_argument("--today"); p.add_argument("--days", type=int, default=7)
    p.add_argument("--tax", type=float, default=core.TAX_DEFAULT); p.add_argument("--ics")
    a = p.parse_args(argv)
    try:
        if not 0 <= a.tax < 1: raise ValueError("세율은 0 이상 1 미만")
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        rows, unk = core.expected(core.read_holdings(a.holdings), core.read_schedule(a.schedule), a.tax)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(rows, unk, today, a.days))
    if a.ics: open(a.ics, "w", encoding="utf-8", newline="").write(core.ics(rows))
    return 0
