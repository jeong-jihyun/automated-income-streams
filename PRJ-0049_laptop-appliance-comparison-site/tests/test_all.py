import os
from datetime import date
import pytest
from comparison import core
from comparison.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
TODAY = date(2026, 10, 27)
D = core.load_products(os.path.join(S, "products.json")); H = core.load_history(os.path.join(S, "prices.csv"))


def test_best_cells_rules():
    b = core.best_cells(D["products"], D["criteria"])
    assert b["무게(kg)"] == {"n1"} and b["메모리(GB)"] == {"n1", "n2"} and b["배터리(시간)"] == {"n1"} and "운영체제" not in b   # 동점은 모두, info 제외


def test_best_needs_two_values():
    assert "x" not in core.best_cells([{"id": "a", "specs": {"x": 1}}], {"x": "higher"})


def test_price_status_alert_lowest_and_drop():
    s = core.price_status(H["n1"], TODAY); assert s["current"] == 1090000 and s["lowest"] == 1090000 and s["alert"] == "기록 중 최저가예요" and s["change_pct"] == -12.8
    two = core.price_status([(date(2026, 10, 20), 100000), (date(2026, 10, 26), 85000)], TODAY); assert "15.0% 내렸어요" in two["alert"]
    assert core.price_status([(date(2026, 10, 26), 100000)], TODAY)["alert"] is None


def test_stale_and_missing():
    assert core.price_status(H["n3"], TODAY)["stale"] and core.price_status([], TODAY)["stale"]


def test_render_content():
    t = core.render(D, H, TODAY)
    assert 'class=best' in t and "1,090,000원" in t and "가격 확인 필요 (26일 전 기록)" in t and "정보 없음" in t and core.DISCLOSURE in t
    assert "<i>예시</i>" not in t and "&lt;i&gt;" in t and "최저 1,090,000원" in t


def test_load_errors(tmp_path):
    with pytest.raises(core.CompareError): core.load_products(str(tmp_path / "none.json"))
    p = tmp_path / "b.json"; p.write_text('{"products":[{}],"criteria":{"a":"best"}}')
    with pytest.raises(core.CompareError, match="higher/lower/info"): core.load_products(str(p))
    c = tmp_path / "h.csv"; c.write_text("id,date,price\nx,not-a-date,1\n")
    with pytest.raises(core.CompareError): core.load_history(str(c))


def test_add_price_and_cli(tmp_path, capsys):
    h = str(tmp_path / "p.csv")
    assert main(["add-price", "n1", "1000000", "--history", h, "--date", "2026-10-27"]) == 0 and main(["add-price", "n1", "-5", "--history", h]) == 2
    assert core.load_history(h)["n1"] == [(date(2026, 10, 27), 1000000)]
    out = str(tmp_path / "c.html")
    assert main(["build", os.path.join(S, "products.json"), "--history", os.path.join(S, "prices.csv"), "--out", out, "--today", "2026-10-27"]) == 0 and os.path.exists(out)
    assert main(["build", str(tmp_path / "none.json")]) == 2
