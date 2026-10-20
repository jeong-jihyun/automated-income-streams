import os
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader
from coloring_book import checker, interior, cover, metadata
from coloring_book.cli import main
from coloring_book.specs import load_specs, trim_size

S = load_specs()
TRIM = trim_size(S, "8.5x11")
W, H = 2550, 3300


def line_art(path, w=W, h=H, bg=255, color=False):
    im = Image.new("RGB", (w, h), (bg, bg, bg))
    d = ImageDraw.Draw(im)
    d.ellipse((w * .2, h * .2, w * .8, h * .8), outline=(255, 0, 0) if color else (0, 0, 0), width=12)
    d.line((w * .3, h * .5, w * .7, h * .5), fill=(0, 0, 0), width=10)
    im.save(path)


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "img"; d.mkdir()
    for i in range(6): line_art(str(d / f"ok{i}.png"))
    line_art(str(d / "small.png"), 600, 800)
    line_art(str(d / "graybg.png"), bg=150)
    Image.new("RGB", (W, H), (255, 255, 255)).save(d / "grayfill.png")
    im = Image.open(d / "grayfill.png"); ImageDraw.Draw(im).rectangle((200, 200, W - 200, H - 200), fill=(128, 128, 128)); im.save(d / "grayfill.png")
    line_art(str(d / "colored.png"), color=True)
    (d / "notes.txt").write_text("x")
    return d


def test_check_folder_finds_problems(folder):
    r = checker.check_folder(str(folder), "8.5x11", S)
    assert r["total"] == 10 and len(r["ok"]) == 6
    assert any("작음" in x for x in r["bad"]["small.png"])
    assert any("흰색이 아님" in x for x in r["bad"]["graybg.png"])
    assert any("회색 면" in x for x in r["bad"]["grayfill.png"])
    assert any("색이 섞" in x for x in r["bad"]["colored.png"])


def test_missing_folder_and_bad_trim(tmp_path):
    with pytest.raises(FileNotFoundError): checker.list_images(str(tmp_path / "none"))
    with pytest.raises(ValueError): trim_size(S, "1x1")


def test_corrupt_image(tmp_path):
    p = tmp_path / "bad.png"; p.write_bytes(b"xx")
    assert "열 수 없음" in checker.check_image(str(p), TRIM, S)[0]


def test_interior_pages_and_size(folder, tmp_path):
    paths = [str(folder / f"ok{i}.png") for i in range(6)]
    out = str(tmp_path / "in.pdf")
    n = interior.build_interior(paths, out, TRIM, S)
    r = PdfReader(out)
    assert n == len(r.pages) == 24  # 12장 → 최소 24쪽
    assert n % 2 == 0
    box = r.pages[0].mediabox
    assert abs(float(box.width) - 8.5 * 72) < 0.5 and abs(float(box.height) - 11 * 72) < 0.5


def test_interior_many_pages_even(folder, tmp_path):
    paths = [str(folder / "ok0.png")] * 15
    n = interior.build_interior(paths, str(tmp_path / "a.pdf"), TRIM, S, blank_back=False)
    assert n == 24
    n2 = interior.build_interior(paths * 2, str(tmp_path / "b.pdf"), TRIM, S, blank_back=False)
    assert n2 == 30


def test_cover_changes_with_pages():
    a = cover.cover_size_in(TRIM, 24, "white", S)
    b = cover.cover_size_in(TRIM, 100, "white", S)
    assert b["spine_in"] > a["spine_in"] and b["width_in"] > a["width_in"]
    assert abs(a["width_in"] - (17 + 24 * 0.002252 + 0.25)) < 1e-3
    assert a["height_in"] == 11.25
    with pytest.raises(ValueError): cover.spine_width_in(10, "neon", S)


def test_cover_pdf_size(tmp_path):
    out = str(tmp_path / "c.pdf")
    s = cover.build_cover(out, "고양이 컬러링북", TRIM, 24, "white", S)
    box = PdfReader(out).pages[0].mediabox
    assert abs(float(box.width) / 72 - s["width_in"]) < 0.01


def test_metadata_limits():
    d = metadata.draft("고양이", 24, S)
    assert len(d["keywords"]) <= S["metadata_keywords_max"] and "고양이" in d["title"]
    assert "AI" in metadata.to_text(d)


def test_cli_end_to_end_and_blocking(folder, tmp_path):
    good = tmp_path / "good"; good.mkdir()
    for i in range(3): line_art(str(good / f"p{i}.png"))
    out = tmp_path / "out"
    assert main(["build", "--input", str(good), "--out", str(out), "--theme", "고양이"]) == 0
    assert (out / "interior.pdf").exists() and (out / "cover.pdf").exists() and (out / "metadata_draft.txt").exists()
    out2 = tmp_path / "out2"
    assert main(["build", "--input", str(folder), "--out", str(out2)]) == 1 and not out2.exists()
    assert main(["check", "--input", str(tmp_path / "nofolder")]) == 2
