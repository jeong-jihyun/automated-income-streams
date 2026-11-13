import datetime as dt, os
import pytest
from pricewatch import core
from pricewatch.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample"); H, T = os.path.join(D, "history.csv"), os.path.join(D, "targets.json")
TODAY = dt.date(2026, 11, 11)


def res():
    h, bad = core.read(H); r = core.analyze(h, core.load_targets(T), TODAY); return {x["item"]: x for x in r}, bad


def test_bad_row_and_same_day_last_wins():
    h, bad = core.read(H); assert bad == [(12, "날짜·상품·가격 형식 오류")]
    assert h["텀블러"] == [(dt.date(2026, 11, 2), 19000)]


def test_drop_and_lowest_alert():
    r, _ = res(); n = r["무선 이어폰"]["notes"]
    assert r["무선 이어폰"]["alert"] and any("하락" in x for x in n) and "기록상 최저가" in n


def test_outlier_suppressed():
    r, _ = res(); assert r["키보드"]["alert"] is False and "입력 오류 의심" in r["키보드"]["notes"][0]


def test_target_alert():
    r, _ = res(); assert r["텀블러"]["alert"] and "목표가 19,500원 이하" in r["텀블러"]["notes"]


def test_stale_warning_not_alert():
    r, _ = res(); assert any("오래됨" in x for x in r["마우스"]["notes"]) and r["마우스"]["alert"] is False


def test_no_alert_if_flat_history():
    r = core.analyze({"a": [(dt.date(2026, 11, 1), 100), (dt.date(2026, 11, 2), 100), (dt.date(2026, 11, 3), 100)]}, today=dt.date(2026, 11, 3))
    assert r[0]["alert"] is False and r[0]["notes"] == []


def test_bad_targets(tmp_path):
    p = tmp_path / "t.json"; p.write_text('{"a": "싸게"}', encoding="utf-8")
    with pytest.raises(ValueError):
        core.load_targets(str(p))


def test_missing_column(tmp_path):
    p = tmp_path / "h.csv"; p.write_text("date,item\n", encoding="utf-8")
    with pytest.raises(ValueError):
        core.read(str(p))


def test_report_states_no_collection():
    h, bad = core.read(H); t = core.report(core.analyze(h, today=TODAY), bad)
    assert "가져오지 않으며" in t and "[제외] 12행" in t


def test_cli(capsys):
    assert main([H, "--targets", T, "--today", "2026-11-11"]) == 0 and "★ 무선 이어폰" in capsys.readouterr().out
    assert main(["nope.csv"]) == 2
