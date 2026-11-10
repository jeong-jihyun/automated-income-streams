import json, os, datetime as dt
import pytest
from coffeesub import core
from coffeesub.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
P = json.load(open(os.path.join(S, "profile.json"), encoding="utf-8")); B = json.load(open(os.path.join(S, "beans.json"), encoding="utf-8"))
T = dt.date(2026, 11, 11)


def test_best_match_first():
    r, _ = core.recommend(P, B, T); assert r[0]["name"] == "에티오피아 예가체프" and r[0]["match"] == 2 and r[0]["match"] <= r[1]["match"]


def test_distance_value():
    assert core.distance(P, B[0]) == 1 + 0 + 1


def test_stale_stock_and_method_skipped():
    _, sk = core.recommend(P, B, T); d = dict(sk)
    assert "제외(너무 오래됨)" in d["케냐 AA"] and "재고 100g 부족" in d["과테말라 안티구아"] and "맞지 않음" in d["브라질 다크"]


def test_freshness_labels():
    assert core.freshness(2).startswith("가스") and core.freshness(10) == "마시기 좋음" and "주의" in core.freshness(35) and core.freshness(60).startswith("제외") and "미래" in core.freshness(-1)


def test_decaf_excluded_by_default_and_allowed_on_request():
    r, sk = core.recommend(P, B, T); assert "디카페 콜롬비아" not in [x["name"] for x in r] and "디카페(요청" in dict(sk)["디카페 콜롬비아"]
    r2, _ = core.recommend(dict(P, allow_decaf=True), B, T); assert r2[0]["name"] == "디카페 콜롬비아"


def test_decaf_only():
    r, _ = core.recommend(dict(P, decaf_only=True), B, T); assert [x["name"] for x in r] == ["디카페 콜롬비아"]


def test_price_scales_with_grams():
    r, _ = core.recommend(dict(P, grams=400), B, T); assert r[0]["price"] == 24000


def test_schedule_skips_weekend_and_cycle():
    ds = core.schedule(P, "2026-11-14")      # 토요일 -> 월요일
    assert ds[0] == dt.date(2026, 11, 16) and all(d.weekday() < 5 for d in ds) and len(ds) == 4
    assert (core.schedule(dict(P, cycle="매월"), "2026-11-02")[1] - dt.date(2026, 11, 2)).days == 28


def test_bad_profile():
    with pytest.raises(ValueError) as e: core.recommend(dict(P, acidity=9, method="뭐든"), B, T)
    assert "acidity" in str(e.value) and "추출 방식" in str(e.value)


def test_future_roast_date_skipped():
    b = [dict(B[0], roasted="2026-12-01")]; r, sk = core.recommend(P, b, T); assert r == [] and "미래" in sk[0][1]


def test_cli(capsys, tmp_path):
    assert main([os.path.join(S, "profile.json"), os.path.join(S, "beans.json"), "--today", "2026-11-11"]) == 0
    o = capsys.readouterr().out; assert "예가체프" in o and "배송 예정일" in o and "결제·배송은 연동하지" in o
    assert main([str(tmp_path / "x.json"), os.path.join(S, "beans.json")]) == 2
