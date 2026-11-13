import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="gasagency", description="앱스 스크립트 의뢰 점검 (배포 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quote"); q.add_argument("csv")
    g = sub.add_parser("gen"); g.add_argument("task", choices=sorted(core.BASE))
    a = p.parse_args(argv)
    try:
        if a.cmd == "quote":
            ok, bad = core.read(a.csv); print(core.report(ok, bad))
        else:
            print(core.skeleton(a.task), end="")
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
