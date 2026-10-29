import os
from datetime import date
import pytest
from subscribe import core
from subscribe.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "data.json")
D = core.load(S); PL = {p["id"]: p for p in D["plans"]}; SUBS = {s["id"]: s for s in D["subscribers"]}


def test_biweekly_dates():
    assert core.ship_dates(date(2026, 10, 6), "biweekly", 3) == [date(2026, 10, 6), date(2026, 10, 20), date(2026, 11, 3)]


def test_monthly_month_end_clamp_and_anchor():
    r = core.ship_dates(date(2026, 1, 31), "monthly", 4); assert r == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31), date(2026, 4, 30)]
    assert core.ship_dates(date(2028, 1, 31), "monthly", 2)[1] == date(2028, 2, 29)               # 윤년
    assert core.ship_dates(date(2026, 12, 15), "monthly", 2)[1] == date(2027, 1, 15)               # 연도 넘김


def test_bad_cycle():
    with pytest.raises(core.SubError): core.ship_dates(date(2026, 1, 1), "daily", 1)


def test_upcoming_skip_pause():
    assert core.upcoming(SUBS["s1"], PL, date(2026, 10, 7), 2) == [date(2026, 10, 20), date(2026, 11, 3)]
    sk = {**SUBS["s1"], "skip": ["2026-10-20"]}; assert core.upcoming(sk, PL, date(2026, 10, 7), 1) == [date(2026, 11, 3)]
    assert core.upcoming(SUBS["s5"], PL, date(2026, 10, 1)) == []


def test_cutoff():
    assert core.can_change(date(2026, 10, 20), date(2026, 10, 17)) and not core.can_change(date(2026, 10, 20), date(2026, 10, 18))
    with pytest.raises(core.SubError, match="3일 전"): core.request_skip(dict(SUBS["s1"]), date(2026, 10, 20), date(2026, 10, 19))
    assert core.request_skip({"id": "x"}, date(2026, 10, 20), date(2026, 10, 10))["skip"] == ["2026-10-20"]


def test_seasonal_box():
    assert [i["name"] for i in core.box(D["items"], date(2026, 10, 20))] == ["사과", "배"] and [i["name"] for i in core.box(D["items"], date(2026, 11, 3))] == ["사과", "귤"]
    with pytest.raises(core.SubError, match="제철 상품이 없어요"): core.box(D["items"], date(2026, 7, 1))


def test_load_check_capacity_and_supply():
    r = core.load_check(D["subscribers"], PL, D["items"], date(2026, 10, 20))
    assert r["shipments"] == 3 and r["by_plan"] == {"p-bi": 3} and r["over_capacity"] == [{"plan": "p-bi", "orders": 3, "capacity": 2}] and r["supply_short"] == []      # s5(일시정지) 제외
    r2 = core.load_check(D["subscribers"], PL, D["items"], date(2026, 11, 3)); assert r2["supply_short"] == []


def test_supply_short():
    items = [{"name": "사과", "months": [10], "supply": 2}]; r = core.load_check(D["subscribers"], PL, items, date(2026, 10, 20)); assert r["supply_short"] == ["사과"]


def test_payment_retry_flow():
    assert core.payment_action(0, None, date(2026, 10, 1)) == {"action": "ok"}
    f = date(2026, 10, 10); assert core.payment_action(1, f, date(2026, 10, 10))["action"] == "wait" and core.payment_action(1, f, date(2026, 10, 11)) == {"action": "retry", "retry_on": date(2026, 10, 11)}
    assert core.payment_action(2, f, date(2026, 10, 13))["action"] == "retry" and core.payment_action(3, f, date(2026, 10, 30))["action"] == "pause"


def test_charge_date():
    assert core.charge_date(date(2026, 10, 20)) == date(2026, 10, 18)


def test_cli(capsys):
    assert main(["schedule", S, "--sub", "s1", "--from", "2026-10-07", "--count", "2"]) == 0 and "배송 2026-10-20 · 결제 2026-10-18" in capsys.readouterr().out
    assert main(["day", S, "2026-10-20"]) == 0 and "물량 초과" in capsys.readouterr().out
    assert main(["skip", S, "--sub", "s1", "--ship", "2026-10-20", "--today", "2026-10-19"]) == 2 and main(["schedule", S, "--sub", "zz", "--from", "2026-10-07"]) == 2
