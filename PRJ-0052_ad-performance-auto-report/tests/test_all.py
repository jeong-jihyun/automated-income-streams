import os, json
from datetime import date
import pytest
from adreport import core
from adreport.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
META = core.load_csv(os.path.join(S, "meta.csv"), "meta"); NAVER = core.load_csv(os.path.join(S, "naver.csv"), "naver")
W = date(2026, 10, 19)


def test_load_and_numbers_with_commas():
    assert len(META) == 28 and META[0]["date"] == date(2026, 10, 12) and META[0]["spend"] >= 20000 and isinstance(META[0]["clicks"], float)


def test_monday():
    assert core.monday(date(2026, 10, 22)) == W and core.monday(W) == W


def test_agg_matches_manual():
    t = core.agg(META, W, "meta"); assert t["spend"] == sum(r["spend"] for r in META if r["date"] >= W) and t["days"] == 7


def test_metrics_safe_division():
    m = core.metrics({"spend": 1000, "impressions": 0, "clicks": 0, "conversions": 0, "value": None, "days": 7})
    assert m["ctr"] is None and m["cpc"] is None and m["cpa"] is None and m["roas"] is None
    m2 = core.metrics({"spend": 1000, "impressions": 10000, "clicks": 100, "conversions": 4, "value": 5000, "days": 7})
    assert m2["ctr"] == 0.01 and m2["cpc"] == 10 and m2["cpa"] == 250 and m2["roas"] == 5


def test_change():
    assert core.change(120, 100) == 20 and core.change(None, 100) is None and core.change(5, 0) is None


def test_flags():
    base = {"spend": 100, "clicks": 500, "conversions": 5, "days": 7, "cpa": 20}
    assert core.flags(base) == [] and any("전환이 0" in f for f in core.flags({**base, "conversions": 0})) and any("30 미만" in f for f in core.flags({**base, "clicks": 10}))
    assert any("2일치" in f for f in core.flags({**base, "days": 2})) and any("30% 이상" in f for f in core.flags({**base, "cpa": 40}, {"cpa": 20}))


def test_report_sections_and_missing_days():
    t = core.report(META + NAVER, W)
    assert "## 전체" in t and "## meta" in t and "## naver" in t and "6일치만" in t and "attribution" in t


def test_report_no_flags_when_clean():
    rows = [{"platform": "meta", "date": date(2026, 10, 19 + i), "campaign": "a", "spend": 1000.0, "impressions": 10000.0, "clicks": 100.0, "conversions": 5.0, "value": 9000.0} for i in range(7)]
    t = core.report(rows, W); assert "특이사항 없음" in t and "6.00x" not in t and "광고수익률(ROAS) | 9.00배" in t


def test_roas_none_without_value_column(tmp_path):
    p = tmp_path / "m.csv"; p.write_text("Day,Amount spent (KRW),Impressions,Link clicks,Results\n2026-10-20,1000,100,10,1\n", encoding="utf-8")
    r = core.load_csv(str(p), "meta"); assert r[0]["value"] is None and "| 광고수익률(ROAS) | - |" in core.report(r, W)


def test_errors(tmp_path):
    p = tmp_path / "x.csv"; p.write_text("a,b\n1,2\n"); 
    with pytest.raises(core.ReportError, match="--map"): core.load_csv(str(p), "meta")
    q = tmp_path / "y.csv"; q.write_text("Day,Amount spent (KRW),Impressions,Link clicks,Results\n2026-10-20,abc,1,1,1\n")
    with pytest.raises(core.ReportError, match="숫자가 아니"): core.load_csv(str(q), "meta")
    q.write_text("Day,Amount spent (KRW),Impressions,Link clicks,Results\n오늘,1,1,1,1\n")
    with pytest.raises(core.ReportError, match="날짜"): core.load_csv(str(q), "meta")
    q.write_text("Day,Amount spent (KRW),Impressions,Link clicks,Results\n2026-10-20,-5,1,1,1\n")
    with pytest.raises(core.ReportError, match="음수"): core.load_csv(str(q), "meta")
    with pytest.raises(core.ReportError): core.load_csv(str(tmp_path / "none.csv"), "meta")


def test_custom_map_and_cli(tmp_path, capsys):
    p = tmp_path / "z.csv"; p.write_text("날짜,비용\n"); 
    c = tmp_path / "c.csv"; c.write_text("d,s,i,c,v\n2026-10-20,1000,100,10,1\n"); mp = tmp_path / "m.json"; mp.write_text(json.dumps({"meta": {"date": "d", "spend": "s", "impressions": "i", "clicks": "c", "conversions": "v"}}))
    out = str(tmp_path / "r.md"); assert main(["--meta", str(c), "--map", str(mp), "--week", "2026-10-22", "--out", out]) == 0 and "# 주간 광고 성과 (2026-10-19" in open(out, encoding="utf-8").read()
    assert main(["--week", "2026-10-19"]) == 2 and main(["--meta", str(tmp_path / "none.csv"), "--week", "2026-10-19"]) == 2
