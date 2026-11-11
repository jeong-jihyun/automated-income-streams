import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="challenge", description="운동 챌린지 인증 검증·환급 계산 (송금하지 않음)")
    p.add_argument("config"); p.add_argument("participants"); p.add_argument("logs"); p.add_argument("--today")
    a = p.parse_args(argv)
    try:
        cfg = core.load_config(a.config); dep = core.read_participants(a.participants)
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        ok, bad = core.verify(a.logs, cfg, dep, today); rows, tot = core.settle(cfg, dep, ok)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.text(rows, tot, bad)); return 0
