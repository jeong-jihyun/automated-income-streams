import argparse, json, sys, datetime as dt
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="coffeesub", description="취향 맞춤 원두 구독 추천")
    p.add_argument("profile"); p.add_argument("beans"); p.add_argument("--today"); p.add_argument("--start")
    a = p.parse_args(argv)
    try:
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        prof = json.load(open(a.profile, encoding="utf-8")); beans = json.load(open(a.beans, encoding="utf-8"))
        pl = core.plan(prof, beans, today, a.start or today.isoformat())
    except (OSError, ValueError, KeyError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(prof, pl)); return 0
