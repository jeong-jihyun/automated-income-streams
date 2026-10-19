import os, tempfile, pytest
from datetime import date
from engine.config import PlannerConfig
from engine.calendar_utils import month_grid, weeks_of_year, days_of_year
from engine.planner import generate
from engine.validate import validate_pdf
from engine.copy_text import make_copy


def test_leap_year_days():
    assert len(list(days_of_year(2028))) == 366
    assert len(list(days_of_year(2027))) == 365


@pytest.mark.parametrize("year", range(2026, 2031))
def test_every_month_calendar(year):
    for ws in ("monday", "sunday"):
        for m in range(1, 13):
            days = [d for w in month_grid(year, m, ws) for d in w if d]
            import calendar
            assert days == list(range(1, calendar.monthrange(year, m)[1]+1))


def test_week_start_alignment():
    for s in weeks_of_year(2027, "monday"): assert s.weekday() == 0
    for s in weeks_of_year(2027, "sunday"): assert (s.weekday()+1) % 7 == 0


def test_weeks_cover_year():
    w = weeks_of_year(2027, "monday")
    assert w[0] <= date(2027,1,1) and w[-1] <= date(2027,12,31)
    assert (date(2027,12,31)-w[-1]).days < 7


def test_config_validation():
    for bad in (dict(year=1999), dict(week_start="friday"), dict(lang="jp"), dict(theme="x"), dict(note_pages=99)):
        with pytest.raises(ValueError): PlannerConfig(**bad).validate()
    with pytest.raises(ValueError): PlannerConfig.check_color("red")


@pytest.mark.parametrize("lang", ["ko", "en"])
def test_pdf_links_valid(lang):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "p.pdf")
        info = generate(PlannerConfig(year=2027, lang=lang, include_daily=False, note_pages=2), out)
        r = validate_pdf(out)
        assert r["broken"] == [] and r["ok"]
        assert r["links"] == info["links"] > 0


def test_full_planner_all_links_resolve():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "full.pdf")
        info = generate(PlannerConfig(year=2028, week_start="sunday"), out)  # 윤년
        r = validate_pdf(out)
        assert r["ok"], r["broken"][:5]
        assert r["pages"] == 2 + 12 + len(weeks_of_year(2028, "sunday")) + 366 + 5
        assert r["size_mb"] < 60


def test_copy_text_mentions_year():
    cfg = PlannerConfig(year=2027)
    t = make_copy(cfg, {"pages": 10, "links": 5})
    assert "2027" in t["title"] and len(t["tags"]) >= 5


def test_links_go_to_the_right_pages():
    """실제 이동 대상 페이지가 설계와 같은지 (출발·도착 쌍 전체 비교)."""
    from engine.validate import link_targets
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "x.pdf")
        info = generate(PlannerConfig(year=2027, include_daily=True), out)
        expected = sorted((s, info["dest_page"][k]) for s, k in info["link_list"])
        actual = sorted((s, t) for s, t in link_targets(out))
        assert expected == actual
        # 연간 페이지(2쪽)의 3월 제목 링크는 3월 월간 페이지로 간다
        assert (2, info["dest_page"]["month_03"]) in actual


def test_validator_detects_broken_link():
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, NameObject, DictionaryObject, NumberObject
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "ok.pdf"); bad = os.path.join(d, "bad.pdf")
        generate(PlannerConfig(year=2027, include_daily=False, include_weekly=False, note_pages=1), out)
        w = PdfWriter(clone_from=out)
        a = w.pages[0]["/Annots"][0].get_object()
        a[NameObject("/Dest")] = ArrayObject([NumberObject(9999), NameObject("/Fit")])
        w.write(bad)
        assert validate_pdf(out)["ok"] and not validate_pdf(bad)["ok"]
