import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="petsit", description="반려동물 돌봄 매칭 (결제·연락 없음)")
    p.add_argument("requests"); p.add_argument("sitters")
    a = p.parse_args(argv)
    try:
        rq, bq = core.read_requests(a.requests); st, bs = core.read_sitters(a.sitters)
        done, left = core.match(rq, st)
        print(core.report(done, left, bq, bs))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
