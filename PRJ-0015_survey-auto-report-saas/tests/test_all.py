import os
import pytest
from survey_report import analyze as an, render
from survey_report.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "survey.csv")


def res(drop=True):
    cols, rows = an.load(SAMPLE)
    return an.analyze(cols, rows, drop)


def test_types_and_stats():
    r = res(); cols = {c["name"]: c for c in r["columns"]}
    assert r["n"] == 6
    assert cols["만족도"]["type"] == "number" and cols["만족도"]["mean"] == round((5+4+3+5+2+4)/6, 2)
    assert cols["만족도"]["median"] == 4 and cols["만족도"]["dist"] == [(2, 1), (3, 1), (4, 2), (5, 2)]
    assert cols["성별"]["type"] == "choice" and dict(cols["성별"]["dist"]) == {"여": 3, "남": 3}
    assert cols["불편한 점"]["type"] == "text" and cols["불편한 점"]["missing"] == 1


def test_pii_detected_and_dropped():
    r = res()
    assert set(r["pii"]) == {"이름", "이메일"} and "이름" not in [c["name"] for c in r["columns"]]
    r2 = res(drop=False)
    assert "이메일" in [c["name"] for c in r2["columns"]] and r2["dropped"] == []


def test_pii_found_by_content_only(tmp_path):
    f = tmp_path / "a.csv"; f.write_text("메모,점수\n연락 010-1234-5678,3\n없음,4\n", encoding="utf-8")
    cols, rows = an.load(str(f))
    assert an.pii_columns(cols, rows) == ["메모"]


def test_keywords_counts_words():
    kw = dict(an.keywords(["배송이 빨라요", "배송이 느려요", "포장이 좋아요"]))
    assert kw["배송"] == 2


def test_load_errors(tmp_path):
    with pytest.raises(an.SurveyError, match="파일이 없"): an.load(str(tmp_path / "x.csv"))
    e = tmp_path / "e.csv"; e.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(an.SurveyError, match="한 줄도"): an.load(str(e))
    d = tmp_path / "d.csv"; d.write_text("a,a\n1,2\n", encoding="utf-8")
    with pytest.raises(an.SurveyError, match="중복"): an.load(str(d))
    k = tmp_path / "k.csv"; k.write_bytes("가,나\n다,라\n".encode("cp949"))
    with pytest.raises(an.SurveyError, match="UTF-8"): an.load(str(k))


def test_bom_csv_ok(tmp_path):
    f = tmp_path / "b.csv"; f.write_bytes("﻿점수\n1\n2\n".encode("utf-8"))
    cols, _ = an.load(str(f)); assert cols == ["점수"]


def test_svg_bar_widths_proportional():
    svg = render.bar_svg([("a", 10), ("b", 5)])
    import re
    w = [int(x) for x in re.findall(r'<rect [^>]*width="(\d+)"', svg)]
    assert w[0] == 2 * w[1] and svg.count("<rect") == 2
    assert render.bar_svg([]) == ""


def test_html_escapes_and_notes_dropped():
    r = res(); r["columns"][0]["name"] = "<script>"
    h = render.html_report(r, "제목&")
    assert "<h2><script>" not in h
    assert "&lt;script&gt;" in h and "제목&amp;" in h and "개인정보로 보이는 열을 보고서에서 뺐습니다" in h
    assert "자주 나온 말" in h


def test_cli_build(tmp_path):
    out = tmp_path / "o"
    assert main(["build", "--csv", SAMPLE, "--out", str(out)]) == 0
    html = (out / "report.html").read_text(encoding="utf-8")
    assert "kim@example.com" not in html and "응답 6건" in html
    from pypdf import PdfReader
    assert len(PdfReader(str(out / "report.pdf")).pages) >= 1
    assert main(["build", "--csv", SAMPLE, "--out", str(tmp_path / "o2"), "--keep-pii"]) == 0
    kept = (tmp_path / "o2" / "report.html").read_text(encoding="utf-8")
    assert "주의: 개인정보로 보이는 열이 포함됩니다" in kept and "개인정보로 보이는 열을 보고서에서 뺐습니다" not in kept


def test_cli_errors(tmp_path):
    assert main(["check", "--csv", str(tmp_path / "none.csv")]) == 2
    assert main(["check", "--csv", SAMPLE]) == 0
