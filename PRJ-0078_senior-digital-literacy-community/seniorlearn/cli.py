import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="seniorlearn", description="시니어 디지털 교육 모임 운영 보조 (결제·채팅 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("enroll"); e.add_argument("learners"); e.add_argument("classes")
    a_ = sub.add_parser("attend"); a_.add_argument("csv")
    a = p.parse_args(argv)
    try:
        if a.cmd == "enroll":
            ls, bl = core.read_learners(a.learners); cs, bc = core.read_classes(a.classes)
            seats, wait, none = core.enroll(ls, cs)
            for c in cs:
                print(core.notice(c, seats[c["id"]], wait[c["id"]])); print()
            if none: print("맞는 수업 없음:", ", ".join(none))
            for n, w in bl + bc: print(f"[제외] {n}행: {w}")
        else:
            for r in core.attendance(a.csv):
                print(f"{r['name']}: 출석률 {r['rate']}% ({r['n']}회)" + (" [연락 권유: 연속 2회 결석]" if r["reach"] else ""))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
