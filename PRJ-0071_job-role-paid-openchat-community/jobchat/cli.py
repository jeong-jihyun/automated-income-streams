import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="jobchat", description="직무별 모임 운영 보조")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report"); r.add_argument("members"); r.add_argument("--today")
    n = sub.add_parser("remind"); n.add_argument("members"); n.add_argument("--today")
    c = sub.add_parser("check"); c.add_argument("text")
    a = p.parse_args(argv)
    try:
        if a.cmd == "check":
            hits = core.check_post(a.text); print("걸린 규칙: " + ", ".join(hits) if hits else "걸린 규칙 없음 (사람이 한 번 더 확인하세요)"); return 0
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today(); ms = core.read_members(a.members)
        if a.cmd == "report": print(core.report(ms, today))
        else:
            for _, t in core.reminders(ms, today): print(t)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
