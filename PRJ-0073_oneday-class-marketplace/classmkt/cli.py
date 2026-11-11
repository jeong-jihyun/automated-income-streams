import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="classmkt", description="원데이 클래스 예약·정산 계산")
    p.add_argument("classes"); p.add_argument("bookings"); p.add_argument("--commission", type=float, default=0.15); p.add_argument("--now")
    a = p.parse_args(argv)
    try:
        if not 0 <= a.commission < 1: raise ValueError("수수료율은 0 이상 1 미만")
        cl = core.load_classes(a.classes); st, log, err = core.process(cl, a.bookings)
        rows, inst = core.settle(cl, st, a.commission, dt.datetime.fromisoformat(a.now) if a.now else None)
    except (OSError, ValueError, KeyError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(rows, inst, log, err)); return 0
