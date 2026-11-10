import datetime as dt, os
import pytest
from divcal import core
from divcal.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); H = os.path.join(S, "holdings.csv"); SC = os.path.join(S, "schedule.csv")
T = dt.date(2026, 11, 11)
ROWS, UNK = core.expected(core.read_holdings(H), core.read_schedule(SC))
R = {r["code"]: r for r in ROWS}


def test_amounts_and_tax():
    assert R["AAA"]["gross"] == 100000 and R["AAA"]["net"] == round(100000 * (1 - 0.154)) == 84600


def test_buy_after_ex_not_eligible():
    assert not R["BBB"]["eligible"] and R["BBB"]["gross"] == 0 and "늦어" in R["BBB"]["why"]


def test_buy_on_ex_date_not_eligible():
    h = {"X": {"name": "엑스", "shares": 1, "buy": dt.date(2026, 11, 13)}}
    rows, _ = core.expected(h, [{"code": "X", "ex": dt.date(2026, 11, 13), "pay": dt.date(2026, 12, 1), "ps": 100.0, "note": ""}]); assert not rows[0]["eligible"]


def test_unknown_code_ignored():
    assert UNK == ["ZZZ"] and "ZZZ" not in R


def test_alert_window():
    a = core.alerts(ROWS, T, 7); assert len(a) == 1 and "D-2" in a[0] and "가상전자" in a[0]
    assert core.alerts(ROWS, dt.date(2026, 12, 1), 7)[0].startswith("[지급 D-4]")
    assert core.alerts(ROWS, dt.date(2027, 6, 1), 7) == []


def test_alert_today_label():
    assert "오늘" in core.alerts(ROWS, dt.date(2026, 11, 13), 0)[0]


def test_monthly_sums():
    assert core.monthly(ROWS) == {"2026-12": 84600, "2027-04": round(75000 * (1 - 0.154))}


def test_ics_has_two_events_per_eligible():
    s = core.ics(ROWS); assert s.count("BEGIN:VEVENT") == 4 and "DTSTART;VALUE=DATE:20261213" not in s and "20261205" in s and s.endswith("\r\n")


def test_bad_inputs(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("code,ex_date,pay_date,per_share\nA,2026-11-20,2026-11-10,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="빠름"): core.read_schedule(str(p))
    p.write_text("code,ex_date,pay_date,per_share\nA,2026/11/20,2026-12-10,100\n", encoding="utf-8")
    with pytest.raises(ValueError, match="형식"): core.read_schedule(str(p))
    p.write_text("code,name,shares,buy_date\nA,가,0,2026-01-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="1 이상"): core.read_holdings(str(p))
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_holdings(str(p))


def test_cli(capsys, tmp_path):
    i = tmp_path / "c.ics"
    assert main([H, SC, "--today", "2026-11-11", "--ics", str(i)]) == 0
    o = capsys.readouterr().out; assert "배당락 D-2" in o and "(제외) 가상금융" in o and "투자 조언이 아닙니다" in o and "ZZZ" in o and i.exists()
    assert main([H, SC, "--tax", "1.5"]) == 2 and main(["없음.csv", SC]) == 2
