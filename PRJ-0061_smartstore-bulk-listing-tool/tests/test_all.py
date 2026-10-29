import csv, json, os
import pytest
from openpyxl import Workbook
from bulklist import core
from bulklist.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); CATS = {"50000100", "50000200"}
X = os.path.join(S, "products.xlsx"); CSV = os.path.join(S, "products.csv")
R = core.run(X, CATS)


def cols(r, row): return {e["col"] for e in r["errors"] if e["row"] == row}


def test_read_xlsx_and_csv_same():
    a, ua = core.read(X); b, ub = core.read(CSV); assert [x["title"] for x in a] == [x["title"] for x in b] and ua == ub == ["메모(무시됨)"] and len(a) == 4 and a[0]["row"] == 2


def test_good_row_passes():
    assert [g["row"] for g in R["good"]] == [2] and R["total"] == 4 and R["bad_rows"] == 3


def test_row3_errors():
    assert cols(R, 3) >= {"title", "price", "desc"} and any("★" in e["msg"] or "특수문자" in e["msg"] for e in R["errors"] if e["row"] == 3)
    assert any("최저가" in e["msg"] for e in R["errors"] if e["row"] == 3) and any("10원 단위" in e["msg"] for e in R["errors"] if e["row"] == 3)


def test_row4_errors():
    c = cols(R, 4); assert {"title", "category", "image", "shipping", "options"} <= c
    assert any("2행과 상품명이 같아요" in e["msg"] for e in R["errors"] if e["row"] == 4) and any("겹쳐요" in e["msg"] for e in R["errors"] if e["row"] == 4)


def test_http_image_and_title_length():
    r = {"row": 2, "title": "가" * 51, "price": "1000", "stock": "1", "category": "50000100", "image": "http://x/a.jpg", "desc": "설명" * 20}
    assert {e["col"] for e in core.validate(r, CATS)} == {"title", "image"}


def test_repeated_word_and_price_formats():
    base = {"row": 2, "title": "셔츠 셔츠 남성", "price": "29,900", "stock": "1", "category": "50000100", "image": "https://x/a.jpg", "desc": "설명" * 20}
    assert [e["msg"] for e in core.validate(base, CATS)] == ["같은 단어가 반복돼요(검색 어뷰징으로 보일 수 있어요)"]
    assert any("숫자만" in e["msg"] for e in core.validate({**base, "title": "셔츠", "price": "2만원"}, CATS)) and any("100원 미만" in e["msg"] for e in core.validate({**base, "title": "셔츠", "price": "50"}, CATS))


def test_parse_options():
    assert core.parse_options("색상:빨강,파랑;사이즈:S,M") == {"색상": ["빨강", "파랑"], "사이즈": ["S", "M"]} and core.parse_options("") == {}
    for bad in ["색상", "색상:", ":빨강", "색상:a,a"]:
        with pytest.raises(core.ListError): core.parse_options(bad)


def test_option_combo_limit():
    o = "a:" + ",".join(str(i) for i in range(11)) + ";b:" + ",".join(str(i) for i in range(10)) + ";c:1,2"
    r = {"row": 2, "title": "t", "price": "1000", "stock": "1", "category": "50000100", "image": "https://x/a.jpg", "desc": "설명" * 20, "options": o}
    assert any("220개" in e["msg"] for e in core.validate(r, CATS))


def test_missing_required_header(tmp_path):
    p = tmp_path / "x.csv"; p.write_text("상품명,판매가\nA,1000\n", encoding="utf-8")
    with pytest.raises(core.ListError, match="필수 열"): core.read(str(p))
    (tmp_path / "e.csv").write_text("")
    with pytest.raises(core.ListError, match="빈 파일"): core.read(str(tmp_path / "e.csv"))
    with pytest.raises(core.ListError): core.read(str(tmp_path / "none.xlsx"))


def test_export_only_good_and_formula_guard(tmp_path):
    out = str(tmp_path / "o.csv"); core.export(R["good"], out); rows = list(csv.reader(open(out, encoding="utf-8-sig")))
    assert len(rows) == 2 and rows[0][0] == "상품명" and rows[1][0].startswith("여름 린넨")
    g = dict(R["good"][0]); g["title"] = "=1+1 셔츠"; core.export([g], out); assert list(csv.reader(open(out, encoding="utf-8-sig")))[1][0].startswith("'=")


def test_blank_rows_skipped(tmp_path):
    p = tmp_path / "b.csv"; p.write_text("상품명,판매가,재고,카테고리,대표이미지,상세설명\n,,,,,\n", encoding="utf-8"); assert core.read(str(p))[0] == []


def test_cli(tmp_path, capsys):
    o, e = str(tmp_path / "ok.csv"), str(tmp_path / "err.csv")
    assert main([X, "--categories", os.path.join(S, "categories.json"), "--out", o, "--errors", e]) == 1
    out = capsys.readouterr().out; assert "전체 4개 중 통과 1개 / 오류 3개 행" in out and "업로드는 하지 않았어요" in out and os.path.exists(o) and len(list(csv.DictReader(open(e, encoding="utf-8-sig")))) >= 8
    assert main([str(tmp_path / "none.csv"), "--categories", os.path.join(S, "categories.json")]) == 2
