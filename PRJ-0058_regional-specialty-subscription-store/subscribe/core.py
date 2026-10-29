"""지역 특산물 정기배송: 배송일 계산, 제철 구성, 주문 마감, 물량(농가 공급량) 점검, 결제 실패 재시도. 모든 자료는 사용자가 넣은 JSON이다."""
import calendar, json
from datetime import date, timedelta

CUTOFF_DAYS = 3      # 배송일 3일 전까지만 변경·건너뛰기 가능(예시)
CHARGE_BEFORE = 2    # 배송 2일 전 결제(예시)
RETRY_AFTER = [1, 3]  # 결제 실패 후 1일, 3일 뒤 재시도, 그래도 실패하면 일시정지
CYCLES = {"weekly": 7, "biweekly": 14, "monthly": None}


class SubError(ValueError):
    pass


def load(path):
    try: return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise SubError(f"파일을 읽지 못했습니다: {e}")


def add_month(d, anchor_day):
    y, m = (d.year, d.month + 1) if d.month < 12 else (d.year + 1, 1)
    return date(y, m, min(anchor_day, calendar.monthrange(y, m)[1]))   # 31일 시작이면 2월은 28/29일


def ship_dates(start, cycle, count):
    if cycle not in CYCLES: raise SubError(f"주기는 {list(CYCLES)} 중 하나여야 해요")
    out, d = [], start
    for _ in range(count):
        out.append(d); d = add_month(d, start.day) if cycle == "monthly" else d + timedelta(days=CYCLES[cycle])
    return out


def upcoming(sub, plans, after, count=4):
    plan = plans[sub["plan"]]; start = date.fromisoformat(sub["start"])
    if sub.get("status", "active") != "active": return []
    skips = set(sub.get("skip", [])); res = []
    for d in ship_dates(start, plan["cycle"], 400):
        if d < after: continue
        if d.isoformat() in skips: continue
        res.append(d)
        if len(res) == count: break
    return res


def can_change(ship, today):
    return (ship - today).days >= CUTOFF_DAYS


def request_skip(sub, ship, today):
    if not can_change(ship, today): raise SubError(f"배송일 {CUTOFF_DAYS}일 전까지만 건너뛸 수 있어요 (배송 {ship}, 오늘 {today})")
    sub.setdefault("skip", []).append(ship.isoformat()); return sub


def box(items, ship):
    out = [i for i in items if ship.month in i["months"]]
    if not out: raise SubError(f"{ship.month}월에 제철 상품이 없어요. 배송을 보류하고 안내하세요")
    return out


def load_check(subs, plans, items, day):
    """그날 배송 물량이 상품별 공급량을 넘는지 확인."""
    count = {}; n = 0
    for s in subs:
        if day in upcoming(s, plans, day, 1) and upcoming(s, plans, day, 1)[0] == day: n += 1; count[s["plan"]] = count.get(s["plan"], 0) + 1
    over = [{"plan": p, "orders": c, "capacity": plans[p].get("capacity")} for p, c in count.items() if plans[p].get("capacity") is not None and c > plans[p]["capacity"]]
    short = [i["name"] for i in box(items, day) if i.get("supply") is not None and i["supply"] < n]
    return {"date": day, "shipments": n, "by_plan": count, "over_capacity": over, "supply_short": short}


def payment_action(fail_count, last_fail, today):
    """결제 실패 처리: 몇 번째 실패인지에 따라 재시도 시점/일시정지."""
    if fail_count == 0: return {"action": "ok"}
    if fail_count > len(RETRY_AFTER): return {"action": "pause", "reason": f"결제가 {fail_count}번 실패해 일시정지해요(고객 안내 필요)"}
    retry_on = last_fail + timedelta(days=RETRY_AFTER[fail_count - 1])
    return {"action": "retry" if today >= retry_on else "wait", "retry_on": retry_on}


def charge_date(ship):
    return ship - timedelta(days=CHARGE_BEFORE)
