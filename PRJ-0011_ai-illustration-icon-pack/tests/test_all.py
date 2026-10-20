import os, shutil, zipfile
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader
from icon_pack import checker, package
from icon_pack.cli import main
from icon_pack.specs import load_specs

S = load_specs()
BLUES = [(30, 60, 140), (60, 110, 190), (20, 30, 80), (120, 160, 220)]


def icon(path, i, size=512, color=None, bg=None, red=False):
    """i 번째 모양: 서로 확실히 다른 14가지 도형."""
    im = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = (220, 40, 40, 255) if red else (*BLUES[i % 4], 255)
    s = size
    shapes = [
        lambda: d.ellipse((s*.1, s*.1, s*.9, s*.9), fill=c),
        lambda: d.rectangle((s*.1, s*.4, s*.9, s*.6), fill=c),
        lambda: d.rectangle((s*.4, s*.1, s*.6, s*.9), fill=c),
        lambda: d.polygon([(s*.5, s*.1), (s*.9, s*.9), (s*.1, s*.9)], fill=c),
        lambda: d.ellipse((s*.1, s*.1, s*.5, s*.5), fill=c),
        lambda: d.ellipse((s*.5, s*.5, s*.9, s*.9), fill=c),
        lambda: d.rectangle((s*.1, s*.1, s*.5, s*.9), fill=c),
        lambda: d.rectangle((s*.5, s*.1, s*.9, s*.9), fill=c),
        lambda: d.polygon([(s*.1, s*.1), (s*.9, s*.1), (s*.5, s*.9)], fill=c),
        lambda: (d.ellipse((s*.1, s*.1, s*.9, s*.9), fill=c), d.ellipse((s*.3, s*.3, s*.7, s*.7), fill=(0, 0, 0, 0))),
        lambda: d.rectangle((s*.1, s*.1, s*.9, s*.3), fill=c),
        lambda: d.rectangle((s*.1, s*.7, s*.9, s*.9), fill=c),
        lambda: (d.rectangle((s*.1, s*.1, s*.9, s*.9), fill=c), d.rectangle((s*.3, s*.3, s*.7, s*.7), fill=(0, 0, 0, 0))),
        lambda: d.polygon([(s*.1, s*.5), (s*.5, s*.1), (s*.9, s*.5), (s*.5, s*.9)], fill=c),
    ]
    shapes[i % len(shapes)]()
    im.save(path)


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "icons"; d.mkdir()
    for i in range(14): icon(str(d / f"icon-{i:02d}.png"), i)
    icon(str(d / "white-bg.png"), 0, bg=(255, 255, 255, 255))   # 불투명 배경 (모서리 채움)
    Image.new("RGB", (512, 512), "white").save(d / "no-alpha.png")   # 알파 없음
    icon(str(d / "Bad Name.png"), 1)                                  # 이름 위반
    icon(str(d / "small-icon.png"), 2, size=256)                      # 작음
    shutil.copy(d / "icon-03.png", d / "icon-03-copy.png")            # 완전 중복
    icon(str(d / "red-style.png"), 5, red=True)                       # 스타일 다름
    return d


def test_check_finds_each_problem(folder):
    r = checker.check_folder(str(folder), S)
    assert r["total"] == 20 and len(r["ok"]) == 14, r["bad"]  # 원본 14개 중 1개(중복 쪽) 제외 + 복사본 1개 통과
    b = r["bad"]
    assert any("모서리" in x for x in b["white-bg.png"])
    assert any("알파" in x for x in b["no-alpha.png"])
    assert any("파일명" in x for x in b["Bad Name.png"])
    assert any("작음" in x for x in b["small-icon.png"])
    # 같은 파일 쌍은 이름 순서상 나중에 나온 쪽에 표시된다 (둘 중 하나만 걸리면 됨)
    dup = [n for n in ("icon-03.png", "icon-03-copy.png") if n in b]
    assert len(dup) == 1 and any("완전히 같은" in x for x in b[dup[0]])
    assert any("대표 색" in x for x in b["red-style.png"])


def test_good_set_has_no_false_positives(tmp_path):
    d = tmp_path / "g"; d.mkdir()
    for i in range(14): icon(str(d / f"icon-{i:02d}.png"), i)
    r = checker.check_folder(str(d), S)
    assert r["bad"] == {} and len(r["ok"]) == 14


def test_errors(tmp_path):
    with pytest.raises(FileNotFoundError): checker.check_folder(str(tmp_path / "no"), S)
    (tmp_path / "e").mkdir()
    with pytest.raises(ValueError): checker.check_folder(str(tmp_path / "e"), S)
    d = tmp_path / "c"; d.mkdir(); (d / "broken.png").write_bytes(b"x")
    assert "열 수 없음" in checker.check_folder(str(d), S)["bad"]["broken.png"][0]


def test_resize_sizes_and_alpha(tmp_path):
    d = tmp_path / "i"; d.mkdir()
    for i in range(3): icon(str(d / f"icon-{i}.png"), i)
    made = package.resize_all(str(d), sorted(os.listdir(d)), str(tmp_path / "o"), S["sizes"])
    assert len(made) == 3 * 4
    for s in S["sizes"]:
        im = Image.open(tmp_path / "o" / "png" / str(s) / "icon-0.png")
        assert im.size == (s, s) and im.mode == "RGBA" and im.getpixel((0, 0))[3] == 0


def test_contact_sheet_cells(tmp_path):
    d = tmp_path / "i"; d.mkdir()
    for i in range(12): icon(str(d / f"icon-{i:02d}.png"), i)
    r = package.contact_sheet(str(d), sorted(os.listdir(d)), str(tmp_path / "s.png"), S["contact_sheet"])
    cs = S["contact_sheet"]
    assert (r["cols"], r["rows"]) == (10, 2)
    assert r["size"] == (10 * cs["cell"] + 11 * cs["gap"], 2 * cs["cell"] + 3 * cs["gap"])


def test_cli_end_to_end_zip_contents(tmp_path):
    d = tmp_path / "i"; d.mkdir()
    for i in range(14): icon(str(d / f"icon-{i:02d}.png"), i)
    out = tmp_path / "out"
    assert main(["build", "--input", str(d), "--out", str(out), "--name", "테스트 팩", "--theme", "미니멀"]) == 0
    z = zipfile.ZipFile(out / "icon_pack.zip")
    names = z.namelist()
    assert "license_guide.pdf" in names and "preview_sheet.png" in names
    assert sum(1 for n in names if n.startswith("png/")) == 14 * 4
    assert len(PdfReader(str(out / "license_guide.pdf")).pages) == 1
    assert "미확인" in (out / "listing_draft.txt").read_text(encoding="utf-8")


def test_cli_blocks_bad_and_missing(folder, tmp_path):
    out = tmp_path / "out2"
    assert main(["build", "--input", str(folder), "--out", str(out)]) == 1 and not out.exists()
    assert main(["check", "--input", str(tmp_path / "none")]) == 2
