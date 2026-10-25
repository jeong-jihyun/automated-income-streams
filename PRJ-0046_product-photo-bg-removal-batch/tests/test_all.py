import os, csv
import numpy as np
import pytest
from PIL import Image, ImageDraw
from photobatch import process as P
from photobatch.batch import run
from photobatch.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")


def img(name): return Image.open(os.path.join(S, name))


def test_mask_finds_product():
    fg, bg = P.foreground_mask(img("cup_plain.jpg"))
    assert 0.1 < fg.mean() < 0.4 and all(abs(a - b) < 6 for a, b in zip(bg, (236, 232, 226)))


def test_output_size_white_bg_and_centered():
    out, info = P.process(img("cup_plain.jpg"), "square_1000")
    assert out.size == (1000, 1000) and info["size"] == (1000, 1000)
    a = np.asarray(out); assert tuple(a[5, 5]) == (255, 255, 255) and tuple(a[995, 995]) == (255, 255, 255)
    ys, xs = np.where((a != 255).any(axis=2)); assert abs((xs.min() + xs.max()) / 2 - 500) < 15 and abs((ys.min() + ys.max()) / 2 - 500) < 15


def test_product_color_kept():
    a = np.asarray(P.process(img("cup_plain.jpg"))[0]).astype(int)
    red = (a[:, :, 0] > a[:, :, 2] + 60); assert red.sum() > 1000                 # 붉은 상품 색이 남아 있음


def test_fill_ratio_within_preset():
    out, _ = P.process(img("cup_plain.jpg"), "market_800"); a = np.asarray(out); ys, xs = np.where((a != 255).any(axis=2))
    assert (xs.max() - xs.min()) <= 800 * 0.80 + 6 and (ys.max() - ys.min()) <= 800 * 0.80 + 6


def test_messy_background_refused():
    with pytest.raises(P.PhotoError, match="단색이 아니"): P.process(img("messy_bg.jpg"))


def test_tiny_unknown_preset_and_no_product():
    with pytest.raises(P.PhotoError, match="너무 작"): P.process(Image.new("RGB", (200, 200), "white"))
    with pytest.raises(P.PhotoError, match="알 수 없는"): P.process(img("cup_plain.jpg"), "nope")
    with pytest.raises(P.PhotoError, match="거의 안 보여"): P.process(Image.new("RGB", (500, 500), (230, 230, 230)))


def test_hole_inside_product_kept():
    im = Image.new("RGB", (600, 600), (235, 235, 235)); g = ImageDraw.Draw(im)
    g.rectangle((150, 150, 450, 450), fill=(40, 90, 160)); g.rectangle((260, 260, 340, 340), fill=(235, 235, 235))  # 안쪽 구멍(배경색과 같음)
    fg, _ = P.foreground_mask(im); assert fg[300, 300]                              # 안쪽은 지우지 않음


def test_batch_report_and_failures(tmp_path):
    rows = run(S, str(tmp_path / "o"))
    st = {r["file"]: r["status"] for r in rows}; assert st == {"bag_blue_bg.png": "ok", "cup_plain.jpg": "ok", "messy_bg.jpg": "fail"}
    assert sorted(os.listdir(tmp_path / "o")) == ["bag_blue_bg.jpg", "cup_plain.jpg", "report.csv"]
    rep = list(csv.DictReader(open(tmp_path / "o" / "report.csv", encoding="utf-8-sig"))); assert any("단색이 아니" in r["reason"] for r in rep)


def test_batch_bad_file_and_dry_run(tmp_path):
    src = tmp_path / "s"; src.mkdir(); (src / "broken.jpg").write_bytes(b"not an image")
    rows = run(str(src), str(tmp_path / "o"), dry_run=True)
    assert rows[0]["status"] == "fail" and "열 수 없" in rows[0]["reason"] and not (tmp_path / "o").exists()
    with pytest.raises(P.PhotoError): run(str(tmp_path / "none"), str(tmp_path / "o"))


def test_cli(tmp_path, capsys):
    assert main([S, str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out; assert "완료 2장 / 실패 1장" in out and "messy_bg.jpg" in out
    assert main([str(tmp_path / "none"), str(tmp_path / "o")]) == 2
