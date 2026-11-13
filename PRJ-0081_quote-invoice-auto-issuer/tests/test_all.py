import json, os
import pytest
from quoteinv import core
from quoteinv.cli import main

SPEC = os.path.join(os.path.dirname(__file__), "..", "sample", "quote.json")


def make_bizno(first9):
    d = [int(c) for c in first9]; w = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    t = sum(a * b for a, b in zip(d, w)) + (d[8] * 5) // 10
    c = (10 - t % 10) % 10; s = first9 + str(c); return f"{s[:3]}-{s[3:5]}-{s[5:]}"


def test_calc_amounts():
    c = core.calc(core.load(SPEC))
    assert c["sub"] == 99999 + 75000 and c["discount"] == 8749 and c["supply"] == 166250 and c["vat"] == 16625 and c["total"] == 182875


def test_rounding_modes():
    d = {"items": [{"name": "a", "qty": 1, "unit_price": 15}], "vat": True, "rounding": "floor"}
    assert core.calc(d)["vat"] == 1
    d["rounding"] = "half_up"; assert core.calc(d)["vat"] == 2


def test_no_vat():
    d = core.load(SPEC); d["vat"] = False; c = core.calc(d); assert c["vat"] == 0 and c["total"] == c["supply"]


def test_korean_amount():
    assert core.korean_amount(182875) == "십팔만이천팔백칠십오"
    assert core.korean_amount(100000000) == "일억" and core.korean_amount(0) == "영" and core.korean_amount(11000) == "일만천"


def test_korean_amount_exact_cases():
    assert core.korean_amount(10000) == "일만" and core.korean_amount(1234) == "천이백삼십사"


def test_numbering_per_month_and_kind():
    ex = ["Q-202611-001", "Q-202611-002", "I-202611-007", "Q-202610-009"]
    assert core.next_number("quote", "2026-11-13", ex) == "Q-202611-003"
    assert core.next_number("invoice", "2026-11-13", ex) == "I-202611-008"
    assert core.next_number("quote", "2026-12-01", ex) == "Q-202612-001"


def test_biz_no():
    good = make_bizno("123456789"); assert core.biz_no_ok(good)
    bad = good[:-1] + str((int(good[-1]) + 1) % 10); assert not core.biz_no_ok(bad) and not core.biz_no_ok("1234567890")


def test_validation_messages():
    with pytest.raises(ValueError) as e:
        core.validate({"type": "x", "date": "2026-13-01", "items": [{"name": "a", "qty": 0, "unit_price": -1}], "discount_pct": 120})
    m = str(e.value)
    for k in ("type", "date", "받는 곳", "공급자", "품목 1", "discount_pct"):
        assert k in m


def test_html_escaped_and_disclaimer():
    d = core.load(SPEC); h = core.render(d, "Q-202611-001", core.calc(d))
    assert "&lt;테스트&gt;상점 &amp; 컴퍼니" in h and "<테스트>" not in h and "전자세금계산서 발행은 하지 않습니다" in h


def test_cli_makes_file_and_increments(tmp_path, capsys):
    out = str(tmp_path / "o")
    assert main([SPEC, "--out", out]) == 0 and main([SPEC, "--out", out]) == 0
    assert sorted(os.listdir(out)) == ["Q-202611-001.html", "Q-202611-002.html", "numbers.json"]
    assert json.load(open(os.path.join(out, "numbers.json"), encoding="utf-8")) == ["Q-202611-001", "Q-202611-002"]


def test_cli_errors(tmp_path):
    p = tmp_path / "b.json"; p.write_text("{", encoding="utf-8")
    assert main([str(p)]) == 2 and main(["nope.json"]) == 2
