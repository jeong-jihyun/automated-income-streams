import csv, os, random
import pytest
from PIL import Image, ImageFilter
from stock_prep import core
from stock_prep.cli import main

CFG = core.load_settings()


def noise_img(path, size, blur=0, fmt="JPEG"):
    random.seed(1)
    small = Image.new("RGB", (size[0] // 8 or 1, size[1] // 8 or 1))
    small.putdata([(random.randint(0, 255),) * 3 for _ in range(small.size[0] * small.size[1])])
    im = small.resize(size, Image.NEAREST)
    # 선명한 경계를 위해 격자 무늬를 한 번 더 섞는다
    im2 = Image.effect_noise(size, 60).convert("RGB")
    im = Image.blend(im, im2, 0.5)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    im.save(path, fmt, quality=95) if fmt == "JPEG" else im.save(path, fmt)


def memo(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["file", "memo", "title"])
        for r in rows: w.writerow(r)


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "photos"; d.mkdir()
    noise_img(str(d / "big.jpg"), (2400, 1800))            # 4.3MP 선명
    noise_img(str(d / "small.jpg"), (800, 600))            # 작음
    noise_img(str(d / "blurry.jpg"), (2400, 1800), blur=12)  # 흐림
    noise_img(str(d / "pic.png"), (2400, 1800), fmt="PNG")  # 형식
    (d / "notes.txt").write_text("hi")
    return d


def test_sharp_big_passes(folder):
    r = core.check_file(str(folder / "big.jpg"), CFG)
    assert r["ok"], r


def test_small_resolution_fails(folder):
    r = core.check_file(str(folder / "small.jpg"), CFG)
    assert not r["ok"] and any("해상도" in p for p in r["problems"])


def test_blurry_detected(folder):
    r = core.check_file(str(folder / "blurry.jpg"), CFG)
    assert any("흐릴" in p for p in r["problems"]), r["info"]


def test_png_format_and_non_image(folder):
    assert any("형식" in p for p in core.check_file(str(folder / "pic.png"), CFG)["problems"])
    assert core.check_file(str(folder / "notes.txt"), CFG)["problems"] == ["이미지 파일이 아닙니다"]


def test_broken_image(tmp_path):
    p = tmp_path / "bad.jpg"; p.write_bytes(b"not an image")
    r = core.check_file(str(p), CFG)
    assert not r["ok"] and "열 수 없습니다" in r["problems"][0]


def test_keywords_dedupe_banned_person_limit():
    kws, warns = core.clean_keywords("Sunset, sunset, beach Nike, woman walking", CFG)
    assert kws.count("sunset") == 1 and "nike" not in kws
    assert any("nike" in w for w in warns) and any("릴리스" in w for w in warns)
    many = ", ".join(f"k{i}" for i in range(80))
    kws2, w2 = core.clean_keywords(many, CFG)
    assert len(kws2) == CFG["keywords"]["max_count"] and any("줄임" in w for w in w2)


def test_prepare_outputs_and_columns(folder, tmp_path):
    memo(tmp_path / "m.csv", [["big.jpg", "sunset, beach, sea", ""], ["small.jpg", "tree", ""],
                              ["blurry.jpg", "river", ""]])
    out = tmp_path / "out"
    r = core.prepare(str(folder), str(tmp_path / "m.csv"), str(out))
    assert r["passed"] == ["big.jpg"]
    assert {n for n, _ in r["failed"]} >= {"small.jpg", "blurry.jpg", "pic.png", "notes.txt"}
    for site, sc in CFG["sites"].items():
        rows = list(csv.reader(open(out / f"metadata_{site}.csv", encoding="utf-8-sig")))
        assert rows[0] == sc["columns"] and len(rows) == 2
    assert "모델 릴리스" in (out / "release_checklist.md").read_text(encoding="utf-8")
    assert "문제 있음" in (out / "report.md").read_text(encoding="utf-8")


def test_empty_folder_and_missing_memo(tmp_path):
    (tmp_path / "e").mkdir()
    memo(tmp_path / "m.csv", [])
    with pytest.raises(ValueError): core.prepare(str(tmp_path / "e"), str(tmp_path / "m.csv"), str(tmp_path / "o"))
    d = tmp_path / "p"; d.mkdir(); noise_img(str(d / "a.jpg"), (2400, 1800))
    with pytest.raises(FileNotFoundError): core.prepare(str(d), str(tmp_path / "nomemo.csv"), str(tmp_path / "o"))


def test_bad_memo_header(tmp_path):
    p = tmp_path / "m.csv"; p.write_text("a,b\n1,2\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_memo(str(p))


def test_cli_exit_codes(folder, tmp_path):
    memo(tmp_path / "m.csv", [["big.jpg", "sunset", ""]])
    assert main([str(folder), str(tmp_path / "m.csv"), str(tmp_path / "o")]) == 1  # 문제 파일 있음
    assert main([str(folder / "nope"), str(tmp_path / "m.csv"), str(tmp_path / "o")]) == 2
