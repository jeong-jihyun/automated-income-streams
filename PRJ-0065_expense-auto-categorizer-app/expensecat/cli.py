import argparse, datetime as dt, json, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="expensecat", description="카드 문자 분류·월간 리포트")
    p.add_argument("sms"); p.add_argument("--rules", required=True); p.add_argument("--mine")
    p.add_argument("--month"); p.add_argument("--today"); p.add_argument("--out")
    p.add_argument("--learn", nargs=2, metavar=("가맹점", "분류"))
    a = p.parse_args(argv)
    try:
        if a.learn:
            if not a.mine: raise ValueError("--learn 은 --mine 파일이 필요합니다")
            core.learn(a.mine, *a.learn); print("규칙 저장:", *a.learn); return 0
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        txs, bad = core.parse(open(a.sms, encoding="utf-8").read(), today)
        rules = json.load(open(a.rules, encoding="utf-8"))
        mine = json.load(open(a.mine, encoding="utf-8")) if a.mine else None
        rep = core.report(txs, rules, mine, a.month)
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print(core.to_text(rep, a.month))
    if bad: print(f"읽지 못한 문자 {len(bad)}건: " + " | ".join(bad))
    if a.out: core.export(rep, a.out)
    return 0
