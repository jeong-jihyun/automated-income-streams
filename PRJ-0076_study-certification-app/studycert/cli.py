import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="studycert", description="공부 시간 기록 검증·랭킹 (사진·위치 확인 없음)")
    p.add_argument("csv"); p.add_argument("--today"); p.add_argument("--since"); p.add_argument("--until")
    a = p.parse_args(argv)
    try:
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        since = dt.date.fromisoformat(a.since) if a.since else today - dt.timedelta(days=6)
        until = dt.date.fromisoformat(a.until) if a.until else today
        ok, bad = core.read(a.csv, today); good, rej = core.validate(ok)
        print(core.report(good, bad, rej, today, since, until))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
