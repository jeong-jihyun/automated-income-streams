import argparse, datetime as dt, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="clubapp", description="소모임 회비·정산·공지 (전송·송금 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dues"); d.add_argument("members"); d.add_argument("payments"); d.add_argument("--month", required=True); d.add_argument("--today")
    s = sub.add_parser("settle"); s.add_argument("expenses")
    n = sub.add_parser("notice"); n.add_argument("--title", required=True); n.add_argument("--when", required=True); n.add_argument("--place", required=True)
    n.add_argument("--rsvp"); n.add_argument("--event"); n.add_argument("--members"); n.add_argument("--today")
    a = p.parse_args(argv)
    try:
        today = dt.date.fromisoformat(a.today) if getattr(a, "today", None) else dt.date.today()
        if a.cmd == "dues":
            rows, unk = core.dues_status(core.read_members(a.members), a.payments, a.month, today)
            for r in rows: print(f"{r['member']}: {r['status']} (낼 돈 {r['due']:,}, 낸 돈 {r['paid']:,}, 남은 돈 {r['left']:,})")
            print(f"합계: 걷힌 돈 {sum(r['paid'] for r in rows):,} / 걷어야 할 돈 {sum(r['due'] for r in rows):,}")
            if unk: print("회원 목록에 없는 입금자: " + ", ".join(unk))
        elif a.cmd == "settle":
            bal = core.balances(a.expenses); t = core.transfers(bal)
            for f, to, amt in t: print(f"{f} → {to}: {amt:,}원")
            print(f"송금 {len(t)}번이면 정산 끝 (잔액 합계 {sum(bal.values())}원)" if t else "정산할 것이 없습니다")
        else:
            ans = core.rsvp(a.rsvp, a.event) if a.rsvp and a.event else None
            mem = list(core.read_members(a.members)) if a.members else None
            print(core.notice(a.title, dt.datetime.fromisoformat(a.when), a.place, today, ans, mem))
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    print("※ 송금·메시지 전송은 하지 않습니다. 문구는 초안입니다."); return 0
