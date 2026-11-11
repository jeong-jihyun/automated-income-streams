import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="sharing", description="동네 나눔·교환 글 점검과 매칭 후보 (연락·거래 없음)")
    p.add_argument("csv"); p.add_argument("--today"); p.add_argument("--max-km", type=float, default=2.0)
    a = p.parse_args(argv)
    try:
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        print(core.report(core.read(a.csv), today, a.max_km))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
