import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="pricewatch", description="가격 기록 점검 (수집 없음)")
    p.add_argument("csv"); p.add_argument("--targets"); p.add_argument("--today")
    a = p.parse_args(argv)
    try:
        hist, bad = core.read(a.csv)
        t = core.load_targets(a.targets) if a.targets else {}
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        print(core.report(core.analyze(hist, t, today), bad))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
