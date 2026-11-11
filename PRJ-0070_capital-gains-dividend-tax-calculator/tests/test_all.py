import datetime as dt, os
import pytest
from taxcalc import core
from taxcalc.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); F = os.path.join(S, "trades.csv")
ROWS = core.read(F); RES, SELLS, LOTS = core.compute(ROWS)


def test_fifo_cost_basis_and_gain():
    # AAPL 15주 매도: 처음 10주(150$, 환율1300, 수수료 5$/10주) + 다음 5주(180$, 1350)
    c1 = (150 * 1300 + 5 * 1300 / 10) * 10; c2 = (180 * 1350 + 5 * 1350 / 10) * 5
    proceeds = 15 * 260 * 1400 - 8 * 1400
    g = [s for s in SELLS if s[1] == "AAPL" and s[0].year == 2025][0][3]
    assert g == round(proceeds - c1 - c2)


def test_remaining_lot_carries_to_next_year():
    # 2025년에 15주를 팔고 남은 5주(두 번째 매수분: 180$, 환율 1350)가 2026년 매도의 취득가가 된다
    cost = 5 * (180 * 1350 + 5 * 1350 / 10); proceeds = 5 * 270 * 1400 - 2 * 1400
    g26 = [s for s in SELLS if s[0].year == 2026][0]
    assert g26[1] == "AAPL" and g26[3] == round(proceeds - cost) and RES[2026]["overseas_gain"] == g26[3] and "AAPL" not in str(LOTS)


def test_overseas_netting_and_deduction():
    r = RES[2025]; assert r["overseas_gain"] == [s for s in SELLS if s[1] == "AAPL" and s[0].year == 2025][0][3] + [s for s in SELLS if s[1] == "NVDA"][0][3]
    assert r["overseas_taxable"] == max(r["overseas_gain"] - 2_500_000, 0) and r["overseas_tax"] == round(r["overseas_taxable"] * 0.22)


def test_domestic_not_taxed_by_default_but_shown():
    r = RES[2025]; assert r["domestic_gain"] == round(100 * 80000 - 500 - (100 * 70000 + 500)) and r["domestic_tax"] == 0
    assert core.compute(ROWS, {"domestic_listed_taxed": True})[0][2025]["domestic_tax"] > 0


def test_dividends_withheld_given_vs_estimated():
    r = RES[2025]; assert r["div_gross"] == round(20 * 0.25 * 1390 + 300000)
    assert r["div_withheld"] == round(0.75 * 1390 + 300000 * 0.154)


def test_oversell_raises():
    rows = core.read(F) + [dict(core.read(F)[0], type="sell", qty=999.0, date=dt.date(2027, 1, 1))]
    with pytest.raises(ValueError, match="보유"): core.compute(rows)


def test_loss_year_warning_and_zero_tax(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("date,type,symbol,market,qty,price,fee,fx\n2025-01-02,buy,X,overseas,1,100,0,1000\n2025-02-02,sell,X,overseas,1,50,0,1000\n", encoding="utf-8")
    r = core.compute(core.read(str(p)))[0][2025]; assert r["overseas_gain"] == -50000 and r["overseas_tax"] == 0 and r["warnings"]


def test_big_dividend_warning(tmp_path):
    p = tmp_path / "t.csv"
    p.write_text("date,type,symbol,market,qty,price,fx\n2025-01-02,dividend,X,domestic,0,25000000,1\n", encoding="utf-8")
    assert "종합과세" in core.compute(core.read(str(p)))[0][2025]["warnings"][0]


def test_bad_input(tmp_path):
    p = tmp_path / "b.csv"
    p.write_text("date,type,symbol,market,qty,price\n2025-01-02,gift,X,overseas,1,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="2행"): core.read(str(p))
    p.write_text("date,type\n", encoding="utf-8")
    with pytest.raises(ValueError, match="필수 열"): core.read(str(p))
    p.write_text("date,type,symbol,market,qty,price\n2025-01-02,buy,X,overseas,0,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="값 오류"): core.read(str(p))


def test_same_day_buy_before_sell(tmp_path):
    p = tmp_path / "s.csv"
    p.write_text("date,type,symbol,market,qty,price\n2025-01-02,sell,X,domestic,1,10\n2025-01-02,buy,X,domestic,1,5\n", encoding="utf-8")
    assert core.compute(core.read(str(p)))[0][2025]["domestic_gain"] == 5


def test_cli(capsys):
    assert main([F]) == 0
    o = capsys.readouterr().out; assert "[2025년]" in o and "[2026년]" in o and "세무 상담이 아닙니다" in o
    assert main(["없음.csv"]) == 2
