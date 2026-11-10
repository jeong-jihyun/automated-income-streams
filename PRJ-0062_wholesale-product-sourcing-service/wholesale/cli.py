import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="wholesale", description="도매 상품 정리·판매가 계산 (등록은 하지 않음)")
    p.add_argument("csv"); p.add_argument("--config"); p.add_argument("--out"); p.add_argument("--hold")
    a = p.parse_args(argv)
    try:
        cfg = json.load(open(a.config, encoding="utf-8")) if a.config else None
        res = core.run(a.csv, cfg)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.summary(res))
    if a.out: core.export_ok(res, a.out)
    if a.hold: core.export_hold(res, a.hold)
    return 0
