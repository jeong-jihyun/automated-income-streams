import os, tempfile, pytest
from openpyxl import load_workbook
from engine.builder import build_template
from engine.check import static_check, check_workbook, recalc, error_values
from engine.presets import PRESETS, KINDS

JOBS = list(PRESETS["jobs"])


def test_invalid_options():
    with tempfile.TemporaryDirectory() as d:
        for bad in (dict(kind="x"), dict(job="x"), dict(theme="x")):
            with pytest.raises(ValueError):
                build_template(out_dir=d, **{"kind": "budget", **bad})


@pytest.mark.parametrize("kind", KINDS)
@pytest.mark.parametrize("job", JOBS)
def test_no_formula_errors_after_recalc(kind, job):
    """모든 종류×직무 조합: 정적 검사 + 재계산 후 오류값 0개."""
    with tempfile.TemporaryDirectory() as d:
        path = build_template(kind, job, "navy", d)
        r = check_workbook(path)
        assert r["recalculated"], "LibreOffice 재계산 실패"
        assert r["static"] == [] and r["errors"] == [], (r["static"][:3], r["errors"][:3])


def _values(kind, job="freelancer"):
    d = tempfile.mkdtemp()
    path = build_template(kind, job, "navy", d)
    rc = recalc(path)
    return load_workbook(rc, data_only=True)


def test_budget_sample_results():
    wb = _values("budget")
    m = wb["월별요약"]
    # 1월: 수입 3,000,000 / 지출 85,000+60,000
    assert (m["B2"].value, m["C2"].value, m["D2"].value) == (3000000, 145000, 2855000)
    # 2월: 수입 2,800,000 / 지출 120,000
    assert (m["B3"].value, m["C3"].value, m["D3"].value) == (2800000, 120000, 2680000)
    assert m["B14"].value == 5800000 and m["C14"].value == 265000 and m["D14"].value == 5535000
    assert abs(m["E2"].value - 2855000/3000000) < 1e-9
    c = wb["분류별지출"]
    assert c["B2"].value == 205000  # 식비 85,000 + 120,000
    assert c["B3"].value == 60000  # 교통


def test_inventory_sample_results():
    wb = _values("inventory")
    r = wb["재고현황"]
    assert [r.cell(2, 5).value, r.cell(3, 5).value, r.cell(4, 5).value] == [15, 7, 60]
    assert r["F2"].value == 15 * 1500
    assert r["G2"].value == "발주 필요"  # 15 <= 안전재고 20
    assert r["G3"].value == "발주 필요"  # 7 <= 10
    assert r["G4"].value == "정상"  # 60 > 50
    assert r["A5"].value in ("", None)  # 빈 행은 비어 있음


def test_project_dashboard_counts():
    """TODAY()에 따라 지연/대기가 달라지므로 날짜와 무관한 값만 확인한다."""
    wb = _values("project")
    d = wb["대시보드"]
    assert d["B2"].value == 4
    assert d["B3"].value == 1  # 진행률 100% → 완료
    assert d["B3"].value + d["B4"].value + d["B5"].value + d["B6"].value == 4
    assert abs(d["B7"].value - (1.0 + 0.5) / 4) < 1e-9
    t = wb["작업목록"]
    assert t["I2"].value == "완료" and t["A2"].value == 1 and t["A6"].value in ("", None)


def test_checker_detects_bad_formulas():
    from openpyxl import Workbook
    with tempfile.TemporaryDirectory() as d:
        wb = Workbook()
        ws = wb.active
        ws.title = "A"
        ws["A1"] = "=1/0"
        ws["A2"] = "=없는시트!A1"
        ws["A3"] = "=B3"  # 오류, 없는 시트, 순환
        p = os.path.join(d, "bad.xlsx")
        wb.save(p)
        r = check_workbook(p)
        assert not r["ok"]
        assert any("없는 시트" in x[2] for x in r["static"])
        assert any(e[1] == "A1" for e in r["errors"])


def test_data_validation_and_guide_sheet():
    with tempfile.TemporaryDirectory() as d:
        wb = load_workbook(build_template("budget", "student", "sage", d))
        assert wb.sheetnames[0] == "사용설명서"
        assert len(wb["거래내역"].data_validations.dataValidation) >= 2
