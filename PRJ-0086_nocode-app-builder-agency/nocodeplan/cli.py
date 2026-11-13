import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="nocodeplan", description="노코드 앱 의뢰 사양 점검")
    p.add_argument("spec")
    a = p.parse_args(argv)
    try:
        d = core.load(a.spec); print(core.report(d)); return 1 if core.check(d)[0] else 0
    except (OSError, ValueError, json.JSONDecodeError, AttributeError) as e:
        print("오류:", e, file=sys.stderr); return 2
