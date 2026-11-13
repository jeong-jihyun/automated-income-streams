import os
import pytest
from reportboard import core
from reportboard.cli import main

DIR = os.path.join(os.path.dirname(__file__), "..", "sample", "reports")


def load():
    rows, bad = core.read_dir(DIR); d, dup = core.merge(rows); return rows, bad, d, dup


def test_bad_line_reported_with_file_and_row():
    rows, bad, *_ = load(); assert bad == [("cs.csv", 5, "숫자 또는 빈 칸 오류")] and len(rows) == 7


def test_comma_number_and_duplicate_last_wins():
    _, _, d, dup = load(); assert d[("영업", "2026-W45", "매출")] == 12000 and dup == 1
    assert d[("고객지원", "2026-W46", "문의수")] == 190


def test_week_over_week():
    *_, d, _ = load(); s = core.summarize(d); row = {r["metric"]: r for r in s["table"]}
    sales = [c for c in row["매출"]["cells"] if c["team"] == "영업"][0]
    assert s["week"] == "2026-W46" and s["prev"] == "2026-W45" and sales["chg"] == 25.0


def test_missing_team_flagged():
    *_, d, _ = load(); assert core.summarize(d, ["영업", "인사"])["missing"] == ["인사"]


def test_new_metric_without_previous_has_no_change(tmp_path):
    (tmp_path / "a.csv").write_text("team,week,metric,value\nA,W1,x,10\nA,W2,x,12\nA,W2,y,5\n", encoding="utf-8")
    rows, _ = core.read_dir(str(tmp_path)); s = core.summarize(core.merge(rows)[0]); row = {r["metric"]: r for r in s["table"]}
    assert row["y"]["cells"][0]["chg"] is None and row["x"]["cells"][0]["chg"] == 20.0


def test_totals():
    *_, d, _ = load(); row = {r["metric"]: r for r in core.summarize(d)["table"]}
    assert row["매출"]["total"] == 15000 and row["문의수"]["total"] == 190


def test_html_escape_and_warning():
    *_, d, _ = load(); s = core.summarize(d, ["<b>팀</b>"]); h = core.render(s)
    assert "&lt;b&gt;팀&lt;/b&gt;" in h and "<b>팀</b>" not in h and "보고가 없는 팀" in h


def test_empty_folder(tmp_path):
    with pytest.raises(ValueError):
        core.read_dir(str(tmp_path))


def test_missing_columns(tmp_path):
    (tmp_path / "a.csv").write_text("x,y\n1,2\n", encoding="utf-8")
    rows, bad = core.read_dir(str(tmp_path)); assert rows == [] and bad[0][2].startswith("열이 없습니다")


def test_cli_writes_file(tmp_path, capsys):
    out = tmp_path / "d.html"; assert main([DIR, "--out", str(out), "--teams", "영업,인사"]) == 0
    t = out.read_text(encoding="utf-8"); assert "2026-W46" in t and "인사" in t and "제외된 줄" in t
    assert main([str(tmp_path / "none")]) == 2
