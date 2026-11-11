import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="taxcalc", description="양도세·배당세 예상 계산")
    p.add_argument("trades"); p.add_argument("--config")
    a = p.parse_args(argv)
    try:
        cfg = json.load(open(a.config, encoding="utf-8")) if a.config else None
        res, sells, _ = core.compute(core.read(a.trades), cfg)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(res, sells)); return 0
