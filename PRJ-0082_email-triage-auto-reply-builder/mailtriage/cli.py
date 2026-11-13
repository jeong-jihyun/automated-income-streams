import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="mailtriage", description="메일 분류·답장 초안 (발송 없음)")
    p.add_argument("mails"); p.add_argument("rules"); p.add_argument("--replied", help="이미 답장한 주소 목록(한 줄에 하나)")
    a = p.parse_args(argv)
    try:
        mails, bad = core.read_mails(a.mails); rules = core.load_rules(a.rules)
        replied = [l.strip().lower() for l in open(a.replied, encoding="utf-8")] if a.replied else []
        sys.stdout.write(core.to_csv(core.process(mails, rules, replied)))
        for n, w in bad: print(f"[제외] {n}행: {w}", file=sys.stderr)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
