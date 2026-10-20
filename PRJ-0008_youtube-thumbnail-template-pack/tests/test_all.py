import json, os
import pytest
from PIL import Image
from pypdf import PdfReader
from thumb_pack import checker, preview, guide_pdf, listing
from thumb_pack.cli import main
from thumb_pack.specs import load_specs, load_pack

S = load_specs()


def solid(path, size, color=(30, 120, 200)):
    Image.new("RGB", size, color).save(path)


def noise(path, size):
    Image.frombytes("RGB", size, os.urandom(size[0] * size[1] * 3)).save(path)


PACK = {"pack_name": "테스트 팩", "theme": "게임", "price_text": "예시",
        "items": [{"file": "thumb_a-01.png", "title": "하나", "canva_url": "https://www.canva.com/design/aaa/view"},
                  {"file": "art_a-01.png", "title": "둘", "canva_url": "https://www.canva.com/design/bbb/view"}],
        "fonts": ["오픈 폰트"]}


@pytest.fixture
def folder(tmp_path):
    d = tmp_path / "png"; d.mkdir()
    for i in range(1, 4): solid(str(d / f"thumb_a-0{i}.png"), (1280, 720))
    solid(str(d / "art_a-01.png"), (2560, 1440))
    solid(str(d / "thumb_wrongsize-01.png"), (1920, 1080))
    solid(str(d / "art_wrongsize-02.png"), (1280, 720))
    noise(str(d / "thumb_big-01.png"), (1280, 720))
    solid(str(d / "My Thumb.png"), (1280, 720))
    return d


def test_check_folder(folder):
    r = checker.check_folder(str(folder), S)
    assert r["total"] == 8 and len(r["ok"]) == 4
    assert any("크기" in x for x in r["bad"]["thumb_wrongsize-01.png"])
    assert any("크기" in x for x in r["bad"]["art_wrongsize-02.png"])
    assert any("용량" in x for x in r["bad"]["thumb_big-01.png"])
    assert any("파일명" in x for x in r["bad"]["My Thumb.png"])


def test_errors(tmp_path):
    with pytest.raises(FileNotFoundError): checker.check_folder(str(tmp_path / "no"), S)
    (tmp_path / "e").mkdir()
    with pytest.raises(ValueError): checker.check_folder(str(tmp_path / "e"), S)
    p = tmp_path / "thumb_bad-01.png"; p.write_bytes(b"x")
    assert "열 수 없음" in checker.check_file(str(p), S)[0]


def test_contact_sheet_cells(folder, tmp_path):
    names = ["thumb_a-01.png", "thumb_a-02.png", "thumb_a-03.png", "art_a-01.png"]
    r = preview.contact_sheet(str(folder), names, str(tmp_path / "s.png"), S)
    assert r["cols"] == 3 and r["rows"] == 2
    cs = S["contact_sheet"]
    assert r["size"][0] == 3 * cs["cell"][0] + 4 * cs["gap"]
    assert Image.open(tmp_path / "s.png").size == tuple(r["size"])


def test_guide_pdf_links_and_pages(tmp_path):
    out = str(tmp_path / "g.pdf")
    n = guide_pdf.build_guide(out, PACK)
    rd = PdfReader(out)
    assert len(rd.pages) == n == 3
    uris = [a.get_object()["/A"]["/URI"] for p in rd.pages for a in (p.get("/Annots") or [])]
    assert uris == [i["canva_url"] for i in PACK["items"]]


def test_listing_counts_and_disclaimer():
    d = listing.draft(PACK, {"thumb": 3, "art": 1})
    assert "썸네일 3개" in d["description"] and "공식 상품이 아닙니다" in d["description"]
    assert "Canva" in listing.to_text(d)


def test_load_pack_errors(tmp_path):
    with pytest.raises(FileNotFoundError): load_pack(str(tmp_path / "x.json"))
    p = tmp_path / "p.json"; p.write_text(json.dumps({"pack_name": "a", "theme": "b", "items": []}))
    with pytest.raises(ValueError): load_pack(str(p))


def test_cli_end_to_end(folder, tmp_path):
    good = tmp_path / "good"; good.mkdir()
    solid(str(good / "thumb_a-01.png"), (1280, 720)); solid(str(good / "art_a-01.png"), (2560, 1440))
    cfg = tmp_path / "pack.json"; cfg.write_text(json.dumps(PACK, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    assert main(["build", "--input", str(good), "--config", str(cfg), "--out", str(out)]) == 0
    assert all((out / f).exists() for f in ("preview_sheet.png", "buyer_guide.pdf", "listing_draft.txt"))
    out2 = tmp_path / "out2"
    assert main(["build", "--input", str(folder), "--config", str(cfg), "--out", str(out2)]) == 1 and not out2.exists()
    assert main(["check", "--input", str(tmp_path / "none")]) == 2
