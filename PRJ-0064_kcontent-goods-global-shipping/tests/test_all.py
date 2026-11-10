import json, os
import pytest
from kgoods import core
from kgoods.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
RT = json.load(open(os.path.join(S, "rates.json"), encoding="utf-8")); RL = json.load(open(os.path.join(S, "rules.json"), encoding="utf-8"))
O = {o["id"]: o for o in core.read_orders(os.path.join(S, "orders.csv"))}
Q = {k: core.quote(v, RT, RL, 1400) for k, v in O.items()}


def test_grouping_orders():
    assert len(O) == 5 and len(O["O1"]["items"]) == 2 and O["O1"]["box"] == {"l": 30.0, "w": 25.0, "h": 10.0}


def test_volume_weight_dominates():
    assert core.vol_weight(50, 40, 30) == 12000 and Q["O5"]["billed_g"] == 12000 and Q["O5"]["volume_g"] == 12000


def test_over_max_weight_blocks_only_that_order():
    assert Q["O5"]["status"] == "발송불가" and "초과" in Q["O5"]["block"][0] and Q["O1"]["status"] == "견적가능"


def test_rate_steps():
    assert core.rate(RT, "일본", 500) == 9000 and core.rate(RT, "일본", 501) == 10200 and core.rate(RT, "일본", 1000) == 15000


def test_unknown_country():
    with pytest.raises(ValueError): core.rate(RT, "화성", 100)


def test_o1_quote():
    q = Q["O1"]; assert q["actual_g"] == 860 and q["billed_g"] == 1500 and q["volume_g"] == 1500 and q["ship_krw"] == 9000 + 10 * 1200 and q["goods_krw"] == 65000
    assert "관세" in q["duty"] or "면세 한도" in q["duty"]


def test_battery_blocked():
    assert Q["O2"]["status"] == "발송불가" and "배터리" in Q["O2"]["block"][0]


def test_unlicensed_blocked():
    assert Q["O3"]["status"] == "발송불가" and "라이선스" in Q["O3"]["block"][0]


def test_banned_category_and_warn():
    assert any("반입 제한" in b for b in Q["O4"]["block"])


def test_duty_over_threshold():
    n = core.duty_note("일본", 150, RL); assert "관세/부가세" in n
    assert "정보 없음" in core.duty_note("독일", 10, RL)


def test_bad_csv(tmp_path):
    p = tmp_path / "b.csv"; p.write_text("id,country\n1,일본\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_orders(str(p))
    p.write_text("id,country,name,category,qty,weight_g,price_krw,licensed\n1,일본,a,앨범,x,1,1,Y\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_orders(str(p))


def test_cli(capsys):
    a = [os.path.join(S, "orders.csv"), "--rates", os.path.join(S, "rates.json"), "--rules", os.path.join(S, "rules.json")]
    assert main(a) == 0
    o = capsys.readouterr().out; assert "[O1]" in o and "발송불가" in o and "발송·결제는 하지 않습니다" in o
    assert main(a + ["--krw-per-usd", "0"]) == 2
    assert main(["없는.csv", "--rates", a[2], "--rules", a[4]]) == 2
