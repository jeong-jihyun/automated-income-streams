import os
from datetime import date
import pytest
from agency import pricing, restrict, orders
from agency.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "rules.json")
R = pricing.load_rules(S)


def test_quote_duty_free():
    q = pricing.quote({"price_usd": 50, "ship_intl_usd": 10, "ship_domestic_krw": 3000, "category": "잡화"}, R)
    assert not q["taxable"] and q["duty"] == 0 and q["vat"] == 0 and q["cost"] == 84000 + 3000


def test_quote_taxable_amounts():
    q = pricing.quote({"price_usd": 150, "ship_intl_usd": 20, "category": "의류"}, R)           # 합계 170달러 > 150달러
    assert q["taxable"] and q["duty"] == round((210000 + 28000) * 0.13) and q["vat"] == round((238000 + q["duty"]) * 0.10) and q["cost"] == 238000 + q["duty"] + q["vat"]


def test_threshold_is_inclusive_free():
    assert not pricing.quote({"price_usd": 140, "ship_intl_usd": 10, "category": "잡화"}, R)["taxable"] and pricing.quote({"price_usd": 140, "ship_intl_usd": 11, "category": "잡화"}, R)["taxable"]


def test_price_covers_fee_and_margin():
    q = pricing.quote({"price_usd": 50, "ship_intl_usd": 10, "category": "잡화"}, R, 20)
    assert q["price"] % 100 == 0 and q["margin_pct"] >= 19.9 and q["profit"] == round(q["price"] * 0.94 - q["cost"])
    assert pricing.quote({"price_usd": 50, "ship_intl_usd": 10, "category": "잡화"}, R)["margin_pct"] >= 14.9


@pytest.mark.parametrize("item,msg", [({"price_usd": 0, "ship_intl_usd": 1, "category": "잡화"}, "0보다"), ({"price_usd": 5, "ship_intl_usd": 1, "category": "없음"}, "알 수 없는 분류"), ({"price_usd": 5, "category": "잡화"}, "ship_intl_usd")])
def test_quote_errors(item, msg):
    with pytest.raises(pricing.PricingError, match=msg): pricing.quote(item, R)


def test_rules_errors(tmp_path):
    (tmp_path / "r.json").write_text('{"usd_krw":1}')
    with pytest.raises(pricing.PricingError): pricing.load_rules(str(tmp_path / "r.json"))
    with pytest.raises(pricing.PricingError): pricing.load_rules(str(tmp_path / "n.json"))


def test_restrict():
    t = {f["type"] for f in restrict.check("아기 비타민 충전기 세트")}; assert t == {"전기·전자", "어린이용품", "식품·건강"}
    assert restrict.check("나이키 에어맥스", ["Nike", "나이키"])[0]["type"] == "브랜드·정품" and restrict.check("머그컵") == []


def test_order_flow_and_history(tmp_path):
    f = str(tmp_path / "o.json"); d = date(2026, 10, 1)
    orders.new(f, "A1", "머그컵", today=d)
    for i, s in enumerate(orders.FLOW[1:], 1): orders.move(f, "A1", s, date(2026, 10, 1 + i))
    assert orders.load(f)["A1"]["status"] == "완료" and len(orders.load(f)["A1"]["history"]) == 7
    with pytest.raises(orders.OrderError, match="바꿀 수 없어요"): orders.move(f, "A1", "접수")


def test_order_rules(tmp_path):
    f = str(tmp_path / "o.json"); orders.new(f, "B", "x")
    with pytest.raises(orders.OrderError, match="이미 있는"): orders.new(f, "B", "x")
    with pytest.raises(orders.OrderError, match="건너뛸 수 없어요"): orders.move(f, "B", "해외발주")
    with pytest.raises(orders.OrderError, match="알 수 없는 상태"): orders.move(f, "B", "이상한")
    with pytest.raises(orders.OrderError, match="없는 주문"): orders.move(f, "Z", "결제확인")
    orders.move(f, "B", "결제확인"); orders.move(f, "B", "취소"); assert orders.load(f)["B"]["status"] == "취소"


def test_cancel_blocked_after_overseas_order(tmp_path):
    f = str(tmp_path / "o.json"); orders.new(f, "C", "x"); orders.move(f, "C", "결제확인"); orders.move(f, "C", "해외발주")
    with pytest.raises(orders.OrderError, match="직접 확인"): orders.move(f, "C", "취소")


def test_late(tmp_path):
    f = str(tmp_path / "o.json"); orders.new(f, "D", "x", today=date(2026, 10, 1)); orders.move(f, "D", "결제확인", date(2026, 10, 1)); orders.move(f, "D", "해외발주", date(2026, 10, 2))
    assert orders.late(f, date(2026, 10, 5)) == [] and orders.late(f, date(2026, 10, 6)) == [{"id": "D", "status": "해외발주", "days": 4, "limit": 3}]


def test_corrupt_file(tmp_path):
    f = tmp_path / "o.json"; f.write_text("{깨짐")
    with pytest.raises(orders.OrderError, match="깨졌"): orders.load(str(f))


def test_cli(tmp_path, capsys):
    assert main(["quote", S, "--price-usd", "50", "--ship-usd", "10", "--category", "잡화"]) == 0 and "판매가" in capsys.readouterr().out
    assert main(["quote", S, "--price-usd", "50", "--category", "없음"]) == 2
    assert main(["check", "아기 충전기"]) == 0 and "[확인 필요]" in capsys.readouterr().out
    f = str(tmp_path / "o.json"); assert main(["order", f, "new", "--id", "X", "--item", "컵"]) == 0 and main(["order", f, "move", "--id", "X", "--status", "완료"]) == 2 and main(["order", f, "list"]) == 0
