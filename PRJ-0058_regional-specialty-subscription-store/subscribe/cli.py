import argparse
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="subscribe", description="지역 특산물 정기배송 일정·물량 점검 (결제·배송 연동 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    a1 = s.add_parser("schedule"); a1.add_argument("data"); a1.add_argument("--sub", required=True); a1.add_argument("--from", dest="after", required=True); a1.add_argument("--count", type=int, default=4)
    a2 = s.add_parser("day"); a2.add_argument("data"); a2.add_argument("date")
    a3 = s.add_parser("skip"); a3.add_argument("data"); a3.add_argument("--sub", required=True); a3.add_argument("--ship", required=True); a3.add_argument("--today", required=True)
    a = p.parse_args(argv)
    try:
        d = core.load(a.data); plans = {x["id"]: x for x in d["plans"]}
        if a.cmd == "schedule":
            sub = next((x for x in d["subscribers"] if x["id"] == a.sub), None)
            if not sub: raise core.SubError(f"없는 구독자: {a.sub}")
            for x in core.upcoming(sub, plans, date.fromisoformat(a.after), a.count): print(f"배송 {x} · 결제 {core.charge_date(x)} · 변경 마감 {x - core.timedelta(days=core.CUTOFF_DAYS)}")
            return 0
        if a.cmd == "day":
            day = date.fromisoformat(a.date); r = core.load_check(d["subscribers"], plans, d["items"], day)
            print(f"{day} 배송 {r['shipments']}건 {r['by_plan']}")
            [print(f"⚠ 물량 초과: {o}") for o in r["over_capacity"]]; [print(f"⚠ 공급 부족: {n}") for n in r["supply_short"]]; return 0
        sub = next((x for x in d["subscribers"] if x["id"] == a.sub), None)
        if not sub: raise core.SubError(f"없는 구독자: {a.sub}")
        core.request_skip(sub, date.fromisoformat(a.ship), date.fromisoformat(a.today)); print("건너뛰기 접수 (이 도구는 파일을 바꾸지 않아요)"); return 0
    except (core.SubError, KeyError, ValueError) as e:
        print(f"[오류] {e}"); return 2
