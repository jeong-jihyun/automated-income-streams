import os, json
from datetime import date
import pytest
from saasguide import core
from saasguide.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "facts.json")
F = core.load(S); TODAY = date(2026, 10, 28)


def test_krw():
    assert core.krw(10, 1400) == 14000 and core.krw(9.99, 1385.5) == 13800


def test_make_disclosure_top_bottom_and_price_table():
    t = core.make(F, TODAY)
    assert t.startswith(core.DISCLOSURE) and t.rstrip().endswith(core.DISCLOSURE) and "| Plus | $10 | 약 14,000원 |" in t and "| Free | 무료 | 0원 |" in t and "| Team | 확인 필요 | - |" in t
    assert "1,400원/달러 (2026-10-27 기준" in t and "부가세는 포함되지 않았어요" in t and t.count("스크린샷") == 2 and "아쉬웠던 점" in t and "일부 어색" in t


def test_stale_warning():
    assert "⚠ 확인한 지" not in core.make(F, TODAY) and "⚠ 확인한 지 40일이" in core.make(F, date(2026, 11, 29))


@pytest.mark.parametrize("patch,msg", [({"tested_on": "2026-12-01"}, "미래"), ({"tested_on": "어제"}, "형식"), ({"cons": []}, "아쉬운 점"), ({"affiliate_link": "http://x"}, "https"), ({"steps": [{"title": "a"}]}, "how"), ({"usd_krw_rate": None}, "환율"), ({"tested_on": ""}, "빠진")])
def test_refuses(patch, msg):
    with pytest.raises(core.GuideError, match=msg): core.make({**F, **patch}, TODAY)


def test_no_plans_ok():
    f = {k: v for k, v in F.items() if k != "plans"}; assert "## 요금" not in core.make(f, TODAY)


def test_check():
    assert core.check(core.make(F, TODAY)) == []
    k = [x for x, _ in core.check("월 $10 무조건 최고의 완벽")]; assert {"고지", "과장", "가격", "스크린샷", "균형"} <= set(k)


def test_load_error_and_cli(tmp_path, capsys):
    with pytest.raises(core.GuideError): core.load("/none.json")
    out = str(tmp_path / "g.md"); assert main(["make", S, "--out", out, "--today", "2026-10-28"]) == 0 and main(["check", out]) == 0
    b = tmp_path / "b.md"; b.write_text("무조건"); assert main(["check", str(b)]) == 1 and main(["make", str(tmp_path / "x.json")]) == 2
