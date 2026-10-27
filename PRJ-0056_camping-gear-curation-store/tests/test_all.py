import os
import pytest
from campset import core
from campset.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "catalog.json")
C = core.load(S)
cat = lambda r, c: next(i for i in r["items"] if i["category"] == c)


def test_qty_needed():
    assert core.qty_needed({"category": "침낭", "capacity": 1}, 3) == 3 and core.qty_needed({"category": "매트", "capacity": 2}, 3) == 2 and core.qty_needed({"category": "텐트"}, 3) == 1


def test_tent_capacity_filter():
    assert [p["id"] for p in core.candidates("텐트", C, 3, "봄가을")] == ["t2"] and [p["id"] for p in core.candidates("텐트", C, 2, "봄가을")] == ["t1", "t2"]
    assert [p["id"] for p in core.candidates("텐트", C, 2, "겨울")] == ["t2"]                            # 계절 제한


def test_sleeping_bag_comfort_rule():
    assert [p["id"] for p in core.candidates("침낭", C, 2, "겨울")] == ["s3"] and [p["id"] for p in core.candidates("침낭", C, 2, "봄가을")] == ["s2", "s3"]
    assert [p["id"] for p in core.candidates("침낭", C, 2, "여름")][0] == "s1"


def test_stock_filter():
    assert core.candidates("침낭", C, 9, "겨울") == []                                                    # 동계 침낭 재고 8 < 9명


def test_min_set_and_budget_failure():
    r = core.build(C, 2, "봄가을", "캠핑", 10000); assert not r["ok"] and r["min_price"] > 10000 and "예산" in r["reason"]


def test_build_within_budget_and_upgrades():
    low = core.build(C, 2, "봄가을", "캠핑", 330000); big = core.build(C, 2, "봄가을", "캠핑", 600000)
    assert low["ok"] and big["ok"] and low["price"] <= 330000 and big["price"] <= 600000 and big["price"] >= low["price"] and low["bundle"]


def test_quantities_for_group():
    r = core.build(C, 4, "봄가을", "캠핑", 900000); assert cat(r, "침낭")["qty"] == 4 and cat(r, "텐트")["id"] == "t2" and cat(r, "텐트")["qty"] == 1 and cat(r, "의자")["qty"] == 4


def test_margin_and_warnings():
    r = core.build(C, 2, "봄가을", "캠핑", 600000); assert r["margin_pct"] == round((r["price"] - r["cost"]) / r["price"] * 100, 1) and r["margin_pct"] > 20
    assert core.build(C, 2, "봄가을", "캠핑", 600000, min_margin_pct=60)["warnings"][0].startswith("마진")
    car = core.build(C, 2, "여름", "차박", 300000); assert car["ok"] and any("햇빛가리개" in w for w in car["warnings"])    # 재고 3, 쓰고 남는 2개(3개 미만)


def test_car_mode_has_no_tent():
    r = core.build(C, 2, "여름", "차박", 300000); assert "텐트" not in {i["category"] for i in r["items"]} and "햇빛가리개" in {i["category"] for i in r["items"]}


def test_missing_category_reported():
    r = core.build([p for p in C if p["category"] != "조명"], 2, "여름", "캠핑", 500000); assert not r["ok"] and r["missing"] == ["조명"]


@pytest.mark.parametrize("args,msg", [((0, "여름", "캠핑", 1), "1명"), ((2, "가을", "캠핑", 1), "계절"), ((2, "여름", "글램핑", 1), "방식")])
def test_arg_errors(args, msg):
    with pytest.raises(core.SetError, match=msg): core.build(C, *args)


def test_load_errors(tmp_path):
    with pytest.raises(core.SetError): core.load(str(tmp_path / "n.json"))
    (tmp_path / "x.json").write_text('[{"id":"a","name":"n","category":"c","cost":10,"price":5,"stock":1}]')
    with pytest.raises(core.SetError, match="원가보다"): core.load(str(tmp_path / "x.json"))


def test_cli(capsys):
    assert main([S, "--persons", "2", "--season", "봄가을", "--budget", "400000"]) == 0 and "세트 가격" in capsys.readouterr().out
    assert main([S, "--persons", "2", "--season", "봄가을", "--budget", "1000"]) == 1 and main([S, "--persons", "0", "--season", "여름", "--budget", "1"]) == 2
