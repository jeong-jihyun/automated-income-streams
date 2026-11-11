import argparse, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="pensionplan", description="연금저축·IRP 월 적립액 계산")
    p.add_argument("profile"); p.add_argument("--config")
    a = p.parse_args(argv)
    try:
        prof = json.load(open(a.profile, encoding="utf-8")); cfg = json.load(open(a.config, encoding="utf-8")) if a.config else None
        print(core.text(prof, core.plan(prof, cfg)))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
