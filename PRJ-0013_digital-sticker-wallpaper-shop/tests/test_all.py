import os, zipfile
import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader
from sticker_shop import checker, process, package
from sticker_shop.cli import main
from sticker_shop.specs import load_specs

S = load_specs()


def blob(path, size=(300, 260), color=(200, 60, 90, 255), margin=40, shape="ellipse"):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = (margin, margin, size[0] - margin, size[1] - margin)
    (d.ellipse if shape == "ellipse" else d.rectangle)(box, fill=color)
    im.save(path)


def photo(path, size=(1600, 2400)):
    im = Image.new("RGB", size)
    ImageDraw.Draw(im).rectangle((0, 0, size[0], size[1] // 2), fill=(90, 140, 220))
    ImageDraw.Draw(im).rectangle((0, size[1] // 2, size[0], size[1]), fill=(240, 180, 90))
    im.save(path)


@pytest.fixture
def stickers(tmp_path):
    d = tmp_path / "st"; d.mkdir()
    for i in range(6): blob(str(d / f"flower-{i:02d}.png"), size=(300 + 20 * i, 260 + 10 * i))
    return d


def test_check_stickers_problems(stickers):
    d = stickers
    Image.new("RGB", (300, 300), "white").save(d / "no-alpha.png")
    blob(str(d / "tiny.png"), size=(100, 100), margin=10)
    Image.new("RGBA", (300, 300), (255, 255, 255, 255)).save(d / "filled.png")
    Image.new("RGBA", (300, 300), (0, 0, 0, 0)).save(d / "empty.png")
    blob(str(d / "Bad Name.png"))
    Image.new("RGB", (300, 300), "red").save(d / "photo.jpg")
    r = checker.check_stickers(str(d), S)
    assert len(r["ok"]) == 6
    b = r["bad"]
    assert "알파" in b["no-alpha.png"][0] and "작음" in b["tiny.png"][0]
    assert "모서리" in b["filled.png"][0] and "전부 투명" in b["empty.png"][0]
    assert "파일명" in b["Bad Name.png"][0] and "PNG" in b["photo.jpg"][0]


def test_check_wallpapers(tmp_path):
    d = tmp_path / "wp"; d.mkdir()
    photo(str(d / "sky-01.jpg")); photo(str(d / "small-01.jpg"), size=(600, 900))
    r = checker.check_wallpapers(str(d), S)
    assert r["ok"] == ["sky-01.jpg"] and "작음" in r["bad"]["small-01.jpg"][0]


def test_folder_errors(tmp_path):
    with pytest.raises(FileNotFoundError): checker.check_stickers(str(tmp_path / "no"), S)
    (tmp_path / "e").mkdir()
    with pytest.raises(ValueError): checker.check_wallpapers(str(tmp_path / "e"), S)


def test_sticker_trim_border_transparent(stickers, tmp_path):
    out = str(tmp_path / "s.png")
    size = process.make_sticker(str(stickers / "flower-00.png"), out, S["sticker"])
    im = Image.open(out)
    st = S["sticker"]
    assert im.size == size and max(size) <= st["max_px"]
    assert im.getpixel((0, 0))[3] == 0                      # 바깥은 투명
    # 원본은 가장자리까지 40px 여백. 자른 뒤 테두리 영역(안쪽 padding 바로 안)에 흰색이 생겨야 함
    p = im.getpixel((st["padding_px"] + 2, size[1] // 2))
    assert p[3] == 255 and p[:3] == (255, 255, 255)
    assert im.getpixel((size[0] // 2, size[1] // 2))[:3] == (200, 60, 90)  # 가운데는 원래 색


def test_sticker_large_is_shrunk(tmp_path):
    p = tmp_path / "big.png"; blob(str(p), size=(2000, 1600), margin=100)
    out = tmp_path / "o.png"
    size = process.make_sticker(str(p), str(out), S["sticker"])
    assert max(size) <= S["sticker"]["max_px"]


def overlaps(a, b):
    return not (a[1] + a[3] <= b[1] or b[1] + b[3] <= a[1] or a[2] + a[4] <= b[2] or b[2] + b[4] <= a[2])


def test_pack_no_overlap_and_in_bounds():
    dims = [(f"s{i:02d}.png", 300 + (i % 5) * 20, 280 + (i % 3) * 30) for i in range(30)]
    cfg = S["sheet"]
    sheets = process.pack_sheets(dims, cfg)
    SW, SH = cfg["size"]; m = cfg["margin"]
    placed = [p for sh in sheets for p in sh]
    assert len(placed) == 30 and {p[0] for p in placed} == {d[0] for d in dims}
    for sh in sheets:
        for p in sh:
            assert p[1] >= m and p[2] >= m and p[1] + p[3] <= SW - m and p[2] + p[4] <= SH - m
        for i in range(len(sh)):
            for j in range(i + 1, len(sh)):
                assert not overlaps(sh[i], sh[j])


def test_pack_multi_sheet_and_too_big():
    small_sheet = {"size": [800, 800], "margin": 20, "gap": 10}
    dims = [(f"s{i}.png", 300, 300) for i in range(9)]
    assert len(process.pack_sheets(dims, small_sheet)) >= 2
    with pytest.raises(ValueError): process.pack_sheets([("big.png", 900, 100)], small_sheet)


def test_wallpapers_sizes(tmp_path):
    p = tmp_path / "w.jpg"; photo(str(p))
    made = process.make_wallpapers(str(p), str(tmp_path / "o"), "w", S["wallpaper"]["sizes"], 90)
    assert [Image.open(m).size for m in made] == [tuple(s) for s in S["wallpaper"]["sizes"]]


def test_cli_end_to_end(stickers, tmp_path):
    wp = tmp_path / "wp"; wp.mkdir(); photo(str(wp / "sky-01.jpg"))
    out = tmp_path / "out"
    assert main(["build", "--stickers", str(stickers), "--wallpapers", str(wp), "--out", str(out), "--name", "테스트", "--theme", "꽃"]) == 0
    names = zipfile.ZipFile(out / "sticker_pack.zip").namelist()
    assert sum(n.startswith("stickers/") for n in names) == 6
    assert "sheets/sheet-01.png" in names and "guide.pdf" in names
    assert sum(n.startswith("wallpapers/") for n in names) == 3
    assert len(PdfReader(str(out / "guide.pdf")).pages) == 1
    assert "미확인" in (out / "listing_draft.txt").read_text(encoding="utf-8")


def test_cli_blocks_and_errors(stickers, tmp_path):
    Image.new("RGB", (300, 300), "white").save(stickers / "no-alpha.png")
    out = tmp_path / "o"
    assert main(["build", "--stickers", str(stickers), "--out", str(out)]) == 1 and not out.exists()
    assert main(["check"]) == 2
    assert main(["check", "--stickers", str(tmp_path / "none")]) == 2
