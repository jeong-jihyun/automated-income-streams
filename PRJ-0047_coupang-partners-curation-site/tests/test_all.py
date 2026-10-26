import os
from datetime import date
import pytest
from curation import site
from curation.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "products.json")
TODAY = date(2026, 10, 27)
P = site.load(S)


def test_validate():
    assert site.validate(P[0], TODAY) == []
    assert any("제휴 링크" in e for e in site.validate(P[3], TODAY)) and any("무조건" in e for e in site.validate(P[4], TODAY))
    assert any("price_date" in e or "확인한 날짜" in e for e in site.validate({"id": "x", "name": "n", "topic": "t", "url": "https://link.coupang.com/a", "price": 100}, TODAY))
    assert site.validate({"id": "x", "name": "n", "topic": "t", "url": "http://link.coupang.com/a"}, TODAY)           # http 거부


def test_price_text_fresh_stale_missing():
    assert "189,000원" in site.price_text(P[0], TODAY) and "변동될 수 있음" in site.price_text(P[0], TODAY)
    assert "가격 확인 필요" in site.price_text(P[1], TODAY) and "329,000" not in site.price_text(P[1], TODAY)
    assert "판매 페이지에서 확인" in site.price_text(P[2], TODAY)


def test_build_pages_and_rejects(tmp_path):
    r = site.build(P, str(tmp_path), TODAY)
    assert r["pages"] == 3 and r["included"] == 3 and {b["id"] for b in r["rejected"]} == {"p4", "p5"}
    assert sorted(os.listdir(tmp_path)) == ["index.html", "계절가전.html", "청소가전.html"]


def test_disclosure_on_every_page_twice(tmp_path):
    site.build(P, str(tmp_path), TODAY)
    for f in os.listdir(tmp_path): assert open(tmp_path / f, encoding="utf-8").read().count(site.DISCLOSURE) == 2


def test_links_rel_and_escape(tmp_path):
    site.build(P, str(tmp_path), TODAY); t = open(tmp_path / "계절가전.html", encoding="utf-8").read()
    assert 'rel="sponsored nofollow noopener"' in t and "<b>선풍기</b>" not in t and "&lt;b&gt;" in t


def test_sorted_by_price_missing_last(tmp_path):
    site.build(P, str(tmp_path), TODAY); t = open(tmp_path / "청소가전.html", encoding="utf-8").read()
    assert t.index("무선 청소기 A") < t.index("로봇청소기 B")


def test_load_errors(tmp_path):
    with pytest.raises(site.CurationError): site.load(str(tmp_path / "none.json"))
    (tmp_path / "x.json").write_text("{}")
    with pytest.raises(site.CurationError): site.load(str(tmp_path / "x.json"))


def test_cli(tmp_path, capsys):
    assert main([S, str(tmp_path / "o"), "--today", "2026-10-27"]) == 0
    o = capsys.readouterr().out; assert "제외: p4" in o and "3개 포함" in o.replace("상품 3개 포함", "3개 포함")
    assert main([str(tmp_path / "none.json"), str(tmp_path / "o")]) == 2
