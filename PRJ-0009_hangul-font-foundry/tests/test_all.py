import os
import pytest
from fontTools.ttLib import TTFont
from PIL import Image, ImageFont
from pypdf import PdfReader
from hangul_font_kit import charset, checker, builder, specimen, svgread
from hangul_font_kit.cli import main

CFG = {"canvas": 1000, "baseline_y": 800, "ascent": 800, "descent": -200, "units_per_em": 1000,
       "advance_hangul": 1000, "advance_other": 600, "advance_space": 300, "family_name": "TestFont",
       "style_name": "Regular", "version": "1.000", "sample_sentence": "가나다 라마"}
SAMPLE = list("가나다라마바사아자차카타파하거너더러머버")
RECT = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 1000"><path d="M100 100 H900 V700 H100 Z"/></svg>'


def write(folder, name, body=RECT):
    (folder / name).write_text(body, encoding="utf-8")


@pytest.fixture
def glyphs(tmp_path):
    d = tmp_path / "g"; d.mkdir()
    for ch in SAMPLE: write(d, f"U+{ord(ch):04X}.svg")
    return d


def test_charset_counts():
    h = charset.ksx1001_hangul()
    assert len(h) == 2350 and len(set(h)) == 2350 and h[0] == "가"
    assert len(charset.required_chars()) == 2350 + len(charset.basic_chars())


def test_charset_csv(tmp_path):
    n = charset.write_csv(str(tmp_path / "c.csv"), ["가", "A"])
    assert n == 2 and "U+AC00.svg" in (tmp_path / "c.csv").read_text(encoding="utf-8-sig")


def test_check_ok_and_missing(glyphs):
    r = checker.check_folder(str(glyphs), CFG, required=SAMPLE + ["힣"])
    assert r["problems"] == [] and len(r["found"]) == 20 and r["missing"] == [ord("힣")]


def test_check_problem_kinds(glyphs):
    write(glyphs, "bad.svg")
    write(glyphs, "U+AC01.svg", RECT.replace("H900", "H1200"))  # 밖으로 나감
    write(glyphs, "U+AC02.svg", RECT.replace(" Z", ""))  # 열린 경로
    write(glyphs, "U+AC03.svg", RECT.replace("0 0 1000 1000", "0 0 500 500"))
    write(glyphs, "U+AC04.svg", RECT.replace("M100 100 H900 V700 H100 Z", "m1 1 l5 5"))  # 상대 좌표
    write(glyphs, "U+AC05.svg", "<svg>")  # 깨진 SVG
    r = checker.check_folder(str(glyphs), CFG, required=SAMPLE)
    msgs = {n: m for n, m in r["problems"]}
    assert "파일명" in msgs["bad.svg"] and "밖으로" in msgs["U+AC01.svg"] and "열린 경로" in msgs["U+AC02.svg"]
    assert "viewBox" in msgs["U+AC03.svg"] and "지원하지" in msgs["U+AC04.svg"] and "형식 오류" in msgs["U+AC05.svg"]


def test_missing_folder():
    with pytest.raises(FileNotFoundError): checker.check_folder("/nonexistent/x", CFG)


def test_parse_curves():
    s = svgread.parse_path("M0 0 C 10 10 20 10 30 0 Q 40 -10 50 0 Z")
    assert s[0]["closed"] and [x[0] for x in s[0]["segs"]] == ["M", "C", "Q"]


def test_build_and_read_back(glyphs, tmp_path):
    r = checker.check_folder(str(glyphs), CFG, required=SAMPLE)
    out = str(tmp_path / "t.ttf")
    assert builder.build_ttf(r["found"], CFG, out) == 20
    f = TTFont(out)
    cmap = f.getBestCmap()
    assert sorted(cmap) == sorted(ord(c) for c in SAMPLE)
    assert f["hmtx"][cmap[ord("가")]][0] == 1000
    assert f["head"].unitsPerEm == 1000
    bb = ImageFont.truetype(out, 100).getbbox("가")
    assert bb[2] - bb[0] > 30  # 실제로 그려짐


def test_build_with_curves(tmp_path):
    d = tmp_path / "c"; d.mkdir()
    write(d, "U+AC00.svg", '<svg viewBox="0 0 1000 1000"><path d="M100 700 C 100 100 900 100 900 700 Z"/></svg>')
    r = checker.check_folder(str(d), CFG, required=["가"])
    assert r["problems"] == []
    builder.build_ttf(r["found"], CFG, str(tmp_path / "c.ttf"))
    assert 0xAC00 in TTFont(str(tmp_path / "c.ttf")).getBestCmap()


def test_specimen_and_pdf(glyphs, tmp_path):
    r = checker.check_folder(str(glyphs), CFG, required=SAMPLE)
    ttf = str(tmp_path / "t.ttf"); builder.build_ttf(r["found"], CFG, ttf)
    sheet = str(tmp_path / "s.png")
    size = specimen.glyph_sheet(ttf, SAMPLE, sheet)
    assert size == (960, 192)
    sen = specimen.sentence_preview(ttf, "가나다 라마 힣", set(SAMPLE), str(tmp_path / "e.png"))
    assert sen["missing"] == ["힣"] and "□" in sen["shown"]
    pdf = str(tmp_path / "p.pdf")
    assert specimen.specimen_pdf(pdf, sheet, str(tmp_path / "e.png")) == 2 == len(PdfReader(pdf).pages)


def test_cli_flow(glyphs, tmp_path):
    out = tmp_path / "out"
    assert main(["build", "--glyphs", str(glyphs), "--out", str(out)]) == 1  # 필수 글자 빠짐
    assert main(["build", "--glyphs", str(glyphs), "--out", str(out), "--allow-missing"]) == 0
    assert all((out / f).exists() for f in ("MyHangulFont.ttf", "glyph_sheet.png", "specimen.pdf", "license_draft.md", "product_draft.md"))
    assert main(["charset", "--out", str(tmp_path / "c.csv")]) == 0
    assert main(["check", "--glyphs", str(tmp_path / "none")]) == 2
