import csv, os
from wholesale import core
from wholesale.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); F = os.path.join(S, "wholesale.csv")
R = core.run(F)


def test_counts_and_ignored():
    assert R["total"] == 6 and len(R["ok"]) == 3 and len(R["hold"]) == 3 and R["ignored"] == ["메모"]


def test_name_cleaned():
    assert R["ok"][0]["name"] == "실리콘 주방 집게 2종 세트"


def test_price_formula():
    # (2500+3000)/(1-0.06-0.15)=6962.0 -> 6970
    assert core.price(2500, 3000, core.DEFAULT) == 6970 and R["ok"][0]["price"] == 6970


def test_profit_not_below_margin():
    for r in R["ok"]:
        assert r["margin_pct"] >= 14.9


def test_banned_and_duplicate_and_low_stock_hold():
    w = {h["row"]: h["why"] for h in R["hold"]}
    assert "금지어" in w[4] and "중복" in w[5] and "재고 2개" in w[6]


def test_brand_watch_warns_not_holds():
    r = [x for x in R["ok"] if "나이키" in x["name"]][0]
    assert "권리 확인" in r["warn"] and "최소주문 5개" in r["warn"]


def test_http_image_warn_and_formula_guard(tmp_path):
    r = [x for x in R["ok"] if x["row"] == 7][0]
    assert "https" in r["warn"]
    p = tmp_path / "o.csv"; core.export_ok(R, str(p))
    rows = list(csv.reader(open(p, encoding="utf-8-sig")))
    assert any(c.startswith("'=HYPERLINK") for row in rows for c in row) and rows[0][2] == "상품명"
    assert "자동 등록하지 않습니다" in rows[-1][0]


def test_bad_config_and_missing_columns(tmp_path):
    p = tmp_path / "x.csv"; p.write_text("상품명,도매가\na,1\n", encoding="utf-8")
    try: core.run(str(p)); assert False
    except ValueError as e: assert "필수 열" in str(e)
    try: core.price(1000, 0, {"fee_rate": .6, "margin_rate": .5, "round_to": 10, "ship_share": 1}); assert False
    except ValueError: pass


def test_cli_outputs(tmp_path, capsys):
    o, h = tmp_path / "o.csv", tmp_path / "h.csv"
    assert main([F, "--config", os.path.join(S, "config.json"), "--out", str(o), "--hold", str(h)]) == 0
    assert "보류" in capsys.readouterr().out and o.exists() and h.exists()
    assert main([str(tmp_path / "none.csv")]) == 2


def test_empty_name_and_bad_numbers(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("도매처,상품명,도매가,최소주문,재고,배송비,이미지\nA,,abc,1,x,-1,\n", encoding="utf-8")
    r = core.run(str(p)); assert not r["ok"] and "상품명이 비어" in r["hold"][0]["why"] and "도매가" in r["hold"][0]["why"]
