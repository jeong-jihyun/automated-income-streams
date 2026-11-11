import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="fxalert", description="기준가 도달 알림 판정 (전송하지 않음)")
    p.add_argument("rules"); p.add_argument("readings"); p.add_argument("--state"); p.add_argument("--outbox"); p.add_argument("--now")
    a = p.parse_args(argv)
    try:
        rules = core.load_rules(a.rules); rd, bad = core.load_readings(a.readings)
        now = dt.datetime.fromisoformat(a.now) if a.now else None
        al, st, notes = core.evaluate(rules, rd, core.load_state(a.state), now)
    except (OSError, ValueError, KeyError) as e:
        print("오류:", e, file=sys.stderr); return 2
    for x in al: print(x["time"][:16], x["text"])
    if not al: print("새로 알릴 것이 없습니다.")
    for n in notes: print("주의:", n)
    if bad: print(f"읽지 못한 가격 {bad}줄을 건너뜀")
    if a.state: core.save_state(a.state, st)
    if a.outbox and al: core.write_outbox(a.outbox, al)
    print("※ 텔레그램·카카오로 보내지 않습니다. outbox 파일에 기록만 합니다. 가격은 사용자가 넣은 값입니다.")
    return 0
