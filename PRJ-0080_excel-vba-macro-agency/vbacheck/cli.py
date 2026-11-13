import argparse, os, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="vbacheck", description="VBA 소스 점검 (실행하지 않음)")
    p.add_argument("files", nargs="+")
    a = p.parse_args(argv)
    worst = 0
    try:
        for f in a.files:
            with open(f, encoding="utf-8-sig", errors="replace") as fh:
                found, n = core.scan(fh.read())
            print(core.report(os.path.basename(f), found, n)); print()
            if any(x["sev"] == core.H for x in found): worst = 1
    except OSError as e:
        print("오류:", e, file=sys.stderr); return 2
    return worst
