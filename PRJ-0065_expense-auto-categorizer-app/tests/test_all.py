import csv, datetime as dt, json, os
import pytest
from expensecat import core
from expensecat.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); T = dt.date(2026, 11, 10)
RULES = json.load(open(os.path.join(S, "rules.json"), encoding="utf-8"))
TXT = open(os.path.join(S, "sms.txt"), encoding="utf-8").read()
TX, BAD = core.parse(TXT, T)


def test_split_and_parse_counts():
    assert len(core.split_messages(TXT)) == 9 and len(TX) == 8 and len(BAD) == 1 and "이벤트" in BAD[0]


def test_fields_shinhan():
    t = TX[0]; assert (t["date"], t["time"], t["kind"], t["amount"], t["merchant"]) == (dt.date(2026, 11, 2), "08:31", "승인", 4500, "스타벅스 강남점")


def test_kb_format_merchant_trimmed():
    t = TX[2]; assert t["amount"] == 12300 and t["merchant"] == "맛나김밥 판교점"


def test_card_number_and_name_not_kept():
    assert all("1234" not in str(t) and "홍*동" not in str(t) for t in TX)


def test_dup_and_cancel_settle():
    a, c, un, dup = core.settle(TX)
    assert dup == 1 and len(c) == 1 and c[0]["merchant"] == "쿠팡" and len(un) == 1 and un[0]["merchant"] == "옛날가게"
    assert all(x["merchant"] != "쿠팡" for x in a)


def test_report_categories_and_total():
    r = core.report(TX, RULES, None, "2026-11")
    assert r["total"] == 4500 + 12300 + 3000 + 18000 and r["by_cat"]["카페"] == 4500 and r["by_cat"]["식비"] == 12300 and r["by_cat"]["편의점"] == 3000
    assert r["uncat"] == ["동네고깃집"] and r["by_cat"]["미분류"] == 18000


def test_user_rules_take_priority():
    r = core.report(TX, RULES, {"외식": ["동네고깃집", "스타벅스"]}, "2026-11"); assert r["by_cat"]["외식"] == 4500 + 18000 and not r["uncat"]


def test_year_rollover():
    tx, _ = core.parse("승인 5,000원 12/30 10:00 카페", dt.date(2026, 1, 2)); assert tx[0]["date"] == dt.date(2025, 12, 30)


def test_invalid_date_unreadable():
    tx, bad = core.parse("승인 5,000원 02/31 10:00 카페", T); assert tx == [] and len(bad) == 1


def test_export_formula_guard(tmp_path):
    tx, _ = core.parse("승인 1,000원 11/01 10:00 =CMD점", T); p = tmp_path / "o.csv"; core.export(core.report(tx, RULES), str(p))
    assert list(csv.reader(open(p, encoding="utf-8-sig")))[1][2] == "'=CMD점"


def test_learn_moves_keyword_atomically(tmp_path):
    p = str(tmp_path / "mine.json"); core.learn(p, "동네고깃집", "식비"); core.learn(p, "동네고깃집", "외식")
    d = json.load(open(p, encoding="utf-8")); assert d["외식"] == ["동네고깃집"] and d["식비"] == []
    assert not [f for f in os.listdir(tmp_path) if f != "mine.json"]


def test_cli(capsys, tmp_path):
    a = [os.path.join(S, "sms.txt"), "--rules", os.path.join(S, "rules.json"), "--today", "2026-11-10", "--month", "2026-11", "--out", str(tmp_path / "o.csv")]
    assert main(a) == 0
    o = capsys.readouterr().out; assert "총 지출 37,800원" in o and "미분류 가맹점" in o and "읽지 못한 문자 1건" in o and (tmp_path / "o.csv").exists()
    assert main(["없음.txt", "--rules", a[2]]) == 2
    assert main([a[0], "--rules", a[2], "--learn", "가게", "식비"]) == 2
