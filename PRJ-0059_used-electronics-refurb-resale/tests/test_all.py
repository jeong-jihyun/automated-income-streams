import json, os
from datetime import date
import pytest
from refurb import core
from refurb.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); TODAY = date(2026, 10, 25)
C = core.load_comps(os.path.join(S, "comps.csv"))
ok = lambda **k: {**{"screen": 0, "body": 0, "battery": 90, "broken": []}, **k}


def test_estimate_filters_window_model_and_outliers():
    e = core.estimate(C, "예시폰 15", TODAY, "128GB")
    assert e["ok"] and e["n"] == 8 and e["outliers"] == 2 and e["used"] == 6 and e["median"] == 527500 and e["low"] == 510000       # 6월 거래·다른 모델 제외
    assert core.estimate(C, "예시폰 15", TODAY, "256GB")["ok"] is False


def test_estimate_not_enough_samples():
    e = core.estimate(C, "예시폰 14", TODAY); assert not e["ok"] and e["n"] == 1 and "최소 5건" in e["reason"]
    with pytest.raises(core.RefurbError, match="시세를 정하기 어려워요"): core.offer(e, core.grade(ok()))


def test_grade_rules():
    assert core.grade(ok())["grade"] == "A" and core.grade(ok(screen=1))["grade"] == "B" and core.grade(ok(battery=82, body=1))["grade"] == "B"
    assert core.grade(ok(screen=2))["grade"] == "C" and core.grade(ok(battery=84))["grade"] == "B" and core.grade(ok(screen=3))["grade"] == "D"
    g = core.grade(ok(broken=["카메라", "충전"])); assert g["grade"] == "D" and g["repair"] == 80000


def test_grade_battery_repair_cost():
    assert core.grade(ok(battery=70))["repair"] == 45000 and core.grade(ok(battery=80))["repair"] == 0


def test_grade_errors():
    with pytest.raises(core.RefurbError, match="screen"): core.grade({"body": 0, "battery": 90})
    with pytest.raises(core.RefurbError, match="알 수 없는 기능"): core.grade(ok(broken=["날개"]))


def test_offer_math():
    e = core.estimate(C, "예시폰 15", TODAY, "128GB"); o = core.offer(e, core.grade(ok(screen=1)))
    assert o["resale"] == round(527500 * 0.9) and o["buy_offer"] % 1000 == 0 and o["expected_profit"] >= 30000 - 1000 and "달라질 수 있어요" in o["note"]
    d = core.offer(e, core.grade(ok(broken=["카메라"]))); assert d["buy_offer"] < o["buy_offer"]


def test_offer_never_negative():
    e = {"ok": True, "median": 50000}; assert core.offer(e, {"factor": 0.6, "repair": 200000})["buy_offer"] == 0


def test_listing_requires_gates():
    gr = core.grade(ok())
    with pytest.raises(core.RefurbError, match="IMEI|분실"): core.listing("예시폰", gr, ok(), {})
    with pytest.raises(core.RefurbError, match="초기화"): core.listing("예시폰", gr, ok(), {"imei_checked": True, "lost_stolen_clear": True})
    t = core.listing("예시폰", gr, ok(screen=1), {"imei_checked": True, "factory_reset_done": True, "lost_stolen_clear": True})
    assert "배터리 성능: 90%" in t and "미세 흠집" in t and "모두 정상" in t and core.check_text(t) == []


def test_listing_discloses_defects():
    gr = core.grade(ok(broken=["스피커"])); t = core.listing("예시폰", gr, ok(broken=["스피커"]), {"imei_checked": True, "factory_reset_done": True, "lost_stolen_clear": True})
    assert "스피커 기능 이상" in t and "D등급" in t


def test_check_text():
    assert len(core.check_text("새것 같은 완벽 상태")) == 2


def test_comps_errors(tmp_path):
    with pytest.raises(core.RefurbError): core.load_comps(str(tmp_path / "n.csv"))
    (tmp_path / "b.csv").write_text("model,price,date\nx,abc,2026-01-01\n")
    with pytest.raises(core.RefurbError, match="2행"): core.load_comps(str(tmp_path / "b.csv"))


def test_cli(capsys):
    assert main(["quote", os.path.join(S, "comps.csv"), "--model", "예시폰 15", "--storage", "128GB", "--check", os.path.join(S, "check_B.json"), "--today", "2026-10-25"]) == 0 and "매입 제안" in capsys.readouterr().out
    assert main(["listing", "--model", "x", "--check", os.path.join(S, "check_B.json")]) == 2
    assert main(["listing", "--model", "x", "--check", os.path.join(S, "check_B.json"), "--imei-checked", "--factory-reset", "--lost-stolen-clear"]) == 0
    assert main(["quote", os.path.join(S, "comps.csv"), "--model", "없는폰", "--check", os.path.join(S, "check_B.json"), "--today", "2026-10-25"]) == 2
