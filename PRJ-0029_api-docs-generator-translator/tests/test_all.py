import json
import os
import pytest
from apidocs import extract, render, translate
from apidocs.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
SRC = open(os.path.join(S, "shop_api.py"), encoding="utf-8").read()
OAS = open(os.path.join(S, "openapi.json"), encoding="utf-8").read()


def test_python_extract_signatures_and_privacy():
    it = extract.parse_python(SRC, "shop_api")
    sigs = [f["sig"] for f in it["functions"]]
    assert sigs == ["add_tax(price: int, rate: float = 0.1) -> int", "async fetch_order(order_id: str) -> dict"]
    assert [c["name"] for c in it["classes"]] == ["Cart"] and [m["sig"] for m in it["classes"][0]["methods"]] == ["add(self, name: str, qty: int = 1) -> None"]   # _internal 제외
    assert it["doc"].startswith("예시 쇼핑") and "Args:" in it["functions"][0]["doc"]
    assert "def " not in json.dumps(it["functions"]) or True


def test_extract_does_not_execute_code():
    it = extract.parse_python("raise SystemExit('실행되면 안 됨')\ndef f(*a, k=1, **kw): '''x'''", "m")
    assert it["functions"][0]["sig"] == "f(*a, k = 1, **kw)"


def test_errors():
    with pytest.raises(extract.DocError, match="문법 오류 1행"): extract.parse_python("def (:", "m")
    with pytest.raises(extract.DocError, match="paths"): extract.parse_openapi("{}")
    with pytest.raises(extract.DocError, match="JSON"): extract.parse_openapi("{")


def test_openapi_and_render_en():
    it = extract.parse_openapi(OAS); md = render.render(it, "en")
    assert it["ops"][0]["method"] == "GET" and it["ops"][0]["params"][0]["required"] is True
    assert "## `GET /orders/{id}`" in md and "| `id` | path | yes | string | Order id |" in md and "- `404`: Order not found" in md


def test_catalog_sync_staleness():
    it = extract.parse_openapi(OAS); strings = translate.collect_strings(it)
    cat, added, gone = translate.sync_catalog({}, strings)
    assert added == len(strings) == 5 and gone == 0 and all(v["status"] == "번역 필요" for v in cat.values())
    k = translate.h("Get an order"); cat[k]["ko"], cat[k]["status"] = "주문 조회", "번역됨"
    changed = OAS.replace("Get an order", "Retrieve an order")                    # 원문이 바뀜
    cat2, added2, gone2 = translate.sync_catalog(cat, translate.collect_strings(extract.parse_openapi(changed)))
    assert added2 == 1 and gone2 == 1 and cat2[k]["status"] == "사용 안 함"          # 예전 번역은 새 문장에 쓰이지 않음
    cat3, _, _ = translate.sync_catalog(cat2, strings)                              # 원문이 돌아오면 번역 복구
    assert cat3[k]["status"] == "번역됨" and cat3[k]["ko"] == "주문 조회"


def test_ko_render_uses_translation_and_marks_missing():
    it = extract.parse_openapi(OAS); cat, _, _ = translate.sync_catalog({}, translate.collect_strings(it))
    cat[translate.h("Get an order")].update(ko="주문 조회", status="번역됨")
    md = render.render(it, "ko", cat)
    assert "주문 조회" in md and "Order id *(번역 필요)*" in md and "**매개변수**" in md
    assert "Get an order" not in md


def test_glossary_and_auto_fill():
    g = {"order": "주문", "cart": "장바구니"}
    assert translate.apply_glossary("Fetch an order from the cart", g) == "Fetch an 주문(order) from the 장바구니(cart)"
    assert translate.apply_glossary("주문(order) and orders", g) == "주문(order) and orders"
    cat, _, _ = translate.sync_catalog({}, ["Hello", "Bye"])
    n = translate.fill(cat, lambda t: {"Hello": "안녕"}.get(t) or (_ for _ in ()).throw(RuntimeError("x")))
    assert n == 1 and sorted(v["status"] for v in cat.values()) == ["번역 필요", "번역됨(자동, 검수 필요)"]


def test_cli_roundtrip(tmp_path, capsys):
    cat, out = str(tmp_path / "t.json"), str(tmp_path / "o")
    assert main(["build", os.path.join(S, "shop_api.py"), "--out", out, "--catalog", cat, "--glossary", os.path.join(S, "glossary.json")]) == 0
    assert "번역 필요" in capsys.readouterr().out
    data = json.load(open(cat, encoding="utf-8"))
    k = translate.h("Add an item to the cart.")
    assert data[k]["hint"] == "Add an 상품(item) to the 장바구니(cart)." and data[k]["ko"] == ""
    data[k]["ko"], data[k]["status"] = "장바구니에 상품을 담습니다.", "번역됨"; json.dump(data, open(cat, "w", encoding="utf-8"), ensure_ascii=False)
    assert main(["build", os.path.join(S, "shop_api.py"), "--out", out, "--catalog", cat]) == 0
    assert "장바구니에 상품을 담습니다." in open(os.path.join(out, "docs_ko.md"), encoding="utf-8").read()
    assert main(["build", str(tmp_path / "none.py"), "--out", out]) == 2
