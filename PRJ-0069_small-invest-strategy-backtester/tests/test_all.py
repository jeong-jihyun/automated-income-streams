import datetime as dt, os
import pytest
from backtest import core
from backtest.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); P = os.path.join(S, "prices.csv")
ROWS = core.load(P)


def series(prices, start=dt.date(2025, 1, 1)):
    return [(start + dt.timedelta(days=i), p) for i, p in enumerate(prices)]


def test_load_ok():
    assert len(ROWS) == 400 and ROWS[0][0] < ROWS[-1][0]


def test_buyhold_no_cost_equals_price_ratio():
    rows = series([100 + i for i in range(80)]); c, a = core.run(rows, "buyhold", cash=1000, fee=0, slip=0)
    assert c[-1][1] == pytest.approx(1000 * 179 / 100) and a.trades == 1


def test_costs_reduce_result():
    rows = series([100 + i for i in range(80)])
    free = core.run(rows, "buyhold", fee=0, slip=0)[0][-1][1]; paid = core.run(rows, "buyhold", fee=0.01, slip=0.01)[0][-1][1]
    assert paid < free


def test_mdd_known():
    c = [(dt.date(2025, 1, i + 1), v) for i, v in enumerate([100, 120, 60, 90])]
    m = core.metrics(c, 100); assert m["mdd"] == pytest.approx(-0.5) and m["total_return"] == pytest.approx(-0.1)


def test_dca_invests_each_month():
    rows = series([100] * 100); c, a = core.run(rows, "dca", monthly=100_000, fee=0, slip=0)
    assert a.invested == 100_000 * 4 and c[-1][1] == pytest.approx(400_000)            # 1/1~4/10 → 4개월


def test_sma_has_no_lookahead():
    # 100 → 급등: 신호가 뜨는 날 종가가 아니라 '다음 날 종가'에 사야 하므로 급등일 이익을 얻을 수 없다
    prices = [100] * 70 + [100.5] + [200] * 10
    c, a = core.run(series(prices), "sma", cash=1000, fee=0, slip=0, fast=5, slow=20)
    assert a.sh > 0 and c[-1][1] < 1000 * 200 / 100.5 * 1.0001 and c[-1][1] == pytest.approx(1000 * 200 / 200)  # 200에 산 뒤 오르지 않았으므로 원금


def test_sma_trades_both_ways():
    c, a = core.run(ROWS, "sma", fast=10, slow=40); assert a.trades >= 2


def test_validation(tmp_path):
    with pytest.raises(ValueError, match="slow"): core.run(ROWS, "sma", fast=50, slow=20)
    with pytest.raises(ValueError, match="월 적립"): core.run(ROWS, "dca")
    with pytest.raises(ValueError, match="전략"): core.run(ROWS, "magic")
    p = tmp_path / "b.csv"
    p.write_text("date,close\n2025-01-02,10\n2025-01-01,11\n", encoding="utf-8")
    with pytest.raises(ValueError, match="오름차순"): core.load(str(p))
    p.write_text("date,close\n2025-01-01,0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="0보다"): core.load(str(p))
    p.write_text("date,close\n2025-01-01,10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="최소"): core.load(str(p))


def test_warnings_gap_and_jump():
    rows = series([100] * 30) + [(dt.date(2025, 3, 20), 100)] ; rows.append((dt.date(2025, 3, 21), 40))
    w = core.warnings(rows); assert any("빠진 구간" in x for x in w) and any("분할·오류" in x for x in w)


def test_compare_and_cli(capsys):
    r = core.compare(ROWS); assert set(r) == {"buyhold", "dca", "sma"} and r["dca"]["invested"] > 0
    assert main([P]) == 0
    o = capsys.readouterr().out; assert "최대낙폭" in o and "투자 조언이 아닙니다" in o and "이동평균" in o
    assert main(["없음.csv"]) == 2
