import csv
import io
import os
import shutil
import pytest
from PIL import Image, ImageDraw, ImageFont
from ocr_app import engine, export, parse
from ocr_app.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
R = open(os.path.join(S, "receipt.txt"), encoding="utf-8").read()
N = open(os.path.join(S, "namecard.txt"), encoding="utf-8").read()


def test_receipt_parse():
    r = parse.parse_receipt(R)
    assert r["store"] == "예시마트 강남점" and r["date"] == "2031-03-05 14:22" and r["biz_no"] == "123-45-67890"
    assert r["items"] == [{"name": "아메리카노", "qty": 2, "amount": 8000}, {"name": "치즈케이크", "qty": 1, "amount": 6500}]
    assert r["total"] == 14500 and r["vat"] == 1318 and r["warnings"] == []


def test_receipt_warnings():
    r = parse.parse_receipt("가게\n사과 1 1,000\n합계 9,999\n")
    assert any("다릅니다" in w for w in r["warnings"]) and any("날짜" in w for w in r["warnings"])
    r2 = parse.parse_receipt("가게\n사과 1 1,000\n")
    assert r2["total"] is None and any("합계" in w for w in r2["warnings"])
    assert parse.parse_receipt("")["store"] is None


def test_namecard_parse():
    c = parse.parse_namecard(N)
    assert c == {"name": "홍길동", "company": "(주)예시컴퍼니", "mobile": "010-1234-5678", "tel": "02-123-4567",
                 "email": "hong@example.com", "address": "서울특별시 예시구 예시로 1", "warnings": []}
    c2 = parse.parse_namecard("Some Corp\nbob@x.org")
    assert c2["email"] == "bob@x.org" and c2["mobile"] is None and any("mobile" in w for w in c2["warnings"])


def test_csv_export_and_formula_guard():
    r = parse.parse_receipt(R)
    rows = list(csv.reader(io.StringIO(export.receipts_csv([r]))))
    assert rows[0] == export.RECEIPT_COLS and rows[1][2] == "아메리카노" and len(rows) == 3
    c = parse.parse_namecard(N); c["name"] = "=HYPERLINK(\"http://evil\")"
    assert list(csv.reader(io.StringIO(export.cards_csv([c]))))[1][0].startswith("'=")
    assert export._safe("-5") == "-5" and export._safe("-cmd") == "'-cmd"


def test_preprocess_upsizes_and_gray(tmp_path):
    Image.new("RGB", (400, 200), (120, 120, 120)).save(tmp_path / "a.png")
    out = engine.preprocess(str(tmp_path / "a.png"), str(tmp_path / "b.png"))
    im = Image.open(out); assert im.mode == "L" and max(im.size) == 1000
    with pytest.raises(engine.OcrError): engine.preprocess(str(tmp_path / "none.png"), str(tmp_path / "x.png"))


@pytest.mark.skipif(not shutil.which("tesseract"), reason="tesseract 없음")
def test_real_ocr_english_receipt(tmp_path):
    """실제 tesseract로 영문·숫자 영수증 이미지를 읽어 본다 (한글은 이 환경에 언어 데이터가 없어 시험 못 함)."""
    img = Image.new("RGB", (900, 420), "white"); d = ImageDraw.Draw(img)
    f = None
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        if os.path.exists(p): f = ImageFont.truetype(p, 44)
    for i, line in enumerate(["EXAMPLE MART", "2031-03-05 14:22", "COFFEE 2 8,000", "TOTAL 14,500"]):
        d.text((40, 30 + i * 90), line, fill="black", font=f)
    img.save(tmp_path / "r.png")
    text = engine.read_text(str(tmp_path / "r.png"), "eng", str(tmp_path))
    r = parse.parse_receipt(text)
    assert "2031-03-05" in (r["date"] or "") and r["total"] == 14500


def test_missing_korean_data_reported(tmp_path):
    langs = engine.available_langs()
    if langs is None or "kor" in langs:
        pytest.skip("조건 해당 없음")
    Image.new("RGB", (50, 50)).save(tmp_path / "a.png")
    with pytest.raises(engine.OcrError, match="언어 데이터가 없습니다: kor"): engine.read_text(str(tmp_path / "a.png"), "kor+eng", str(tmp_path))


def test_cli_txt_inputs(tmp_path, capsys):
    out = tmp_path / "o.csv"
    assert main(["receipt", os.path.join(S, "receipt.txt"), "--out", str(out)]) == 0 and "항목 모두 찾음" in capsys.readouterr().out
    assert out.read_bytes().startswith(b"\xef\xbb\xbf")                    # 엑셀용 BOM
    assert main(["namecard", os.path.join(S, "namecard.txt"), "--out", str(tmp_path / "n.csv")]) == 0
    assert main(["receipt", str(tmp_path / "none.txt"), "--out", str(out)]) == 2
