import http.client
import json
import os
import threading
from http.server import HTTPServer
import pytest
from kr_gateway import adapters, server
from kr_gateway.cli import demo_fetchers, main
from kr_gateway.gateway import Gateway, GatewayError

S = os.path.join(os.path.dirname(__file__), "..", "sample")
MAPS = adapters.load_mappings(os.path.join(S, "mappings.json"))
KEYS = {"k": {"owner": "t", "rate_per_min": 3}}


def gw(clock=lambda: 0.0, fetchers=None):
    return Gateway(KEYS, MAPS, fetchers or demo_fetchers(), clock)


def test_normalize_three_channels_sorted():
    r = gw().orders("k")
    assert [o["order_id"] for o in r["orders"]] == ["77", "N1", "K9"]       # 최신순
    assert {o["channel"]: o["status"] for o in r["orders"]} == {"naver": "paid", "coupang": "paid", "kakao": "delivered"}
    assert r["orders"][1]["amount"] == 12000 and r["orders"][0]["buyer"] == "나" and r["errors"] == {}


def test_unknown_status_and_skipped_rows():
    items, skipped = adapters.normalize("naver", {"data": {"orders": [
        {"orderId": "1", "orderStatus": "???", "totalPaymentAmount": 100, "orderDate": "d"},
        {"orderStatus": "PAYED", "totalPaymentAmount": 1},                    # id 없음
        {"orderId": "3", "totalPaymentAmount": "많음"}]}}, MAPS["naver"])
    assert [i["status"] for i in items] == ["unknown"] and skipped == 2


def test_format_change_reported():
    with pytest.raises(adapters.AdapterError, match="찾지 못했습니다"): adapters.normalize("naver", {"x": 1}, MAPS["naver"])
    with pytest.raises(adapters.AdapterError, match="배열"): adapters.normalize("naver", {"data": {"orders": {}}}, MAPS["naver"])


def test_auth_and_rate_limit_window():
    t = [0.0]; g = gw(lambda: t[0])
    with pytest.raises(GatewayError) as e: g.orders("bad"); 
    assert e.value.code == 401
    for _ in range(3): g.orders("k")
    with pytest.raises(GatewayError) as e: g.orders("k")
    assert e.value.code == 429
    t[0] = 61; g.orders("k")                                                 # 1분 뒤 다시 허용
    assert g.usage["k"] == 4


def test_cache_and_partial_failure():
    calls = {"n": 0}; f = demo_fetchers()
    def boom(): raise RuntimeError("timeout")
    base = f["naver"]
    def counted(): calls["n"] += 1; return base()
    f["naver"], f["kakao"] = counted, boom
    t = [0.0]; g = Gateway({"k": {"owner": "t", "rate_per_min": 99}}, MAPS, f, lambda: t[0], cache_sec=30)
    r = g.orders("k"); g.orders("k")
    assert calls["n"] == 1 and "kakao" in r["errors"] and len(r["orders"]) == 2   # 캐시 + 한 채널 실패해도 나머지 반환
    t[0] = 31; g.orders("k"); assert calls["n"] == 2


def test_all_channels_fail_not_billed():
    f = {c: (lambda: (_ for _ in ()).throw(RuntimeError("x"))) for c in MAPS}
    g = gw(fetchers=f); r = g.orders("k")
    assert r["orders"] == [] and len(r["errors"]) == 3 and g.usage["k"] == 0
    with pytest.raises(GatewayError, match="지원하지 않는") as e: g.orders("k", ["shopee"])
    assert e.value.code == 400


def test_mapping_validation(tmp_path):
    def w(m): p = tmp_path / "m.json"; p.write_text(json.dumps(m), encoding="utf-8"); return str(p)
    spec = dict(MAPS["naver"])
    with pytest.raises(adapters.AdapterError, match="공통 상태"): adapters.load_mappings(w({"n": dict(spec, status_map={"A": "weird"})}))
    bad = {k: v for k, v in spec.items() if k != "id"}
    with pytest.raises(adapters.AdapterError, match="'id'"): adapters.load_mappings(w({"n": bad}))
    with pytest.raises(adapters.AdapterError): adapters.load_mappings(str(tmp_path / "no.json"))


def test_http_endpoints():
    httpd = HTTPServer(("127.0.0.1", 0), server.make_handler(gw()))
    port = httpd.server_address[1]; threading.Thread(target=httpd.serve_forever, daemon=True).start()
    def get(path, key="k"):
        c = http.client.HTTPConnection("127.0.0.1", port); c.request("GET", path, headers={"X-API-Key": key} if key else {})
        r = c.getresponse(); return r.status, json.loads(r.read())
    try:
        st, d = get("/v1/orders?channel=naver,kakao"); assert st == 200 and len(d["orders"]) == 2
        assert get("/v1/orders", None)[0] == 401 and get("/v1/orders?channel=x")[0] == 400
        assert get("/v1/usage")[1]["calls"] >= 1 and get("/nope")[0] == 404
        assert get("/v1/orders")[0] == 429                                # 한도 3회: orders, usage 호출 포함
    finally:
        httpd.shutdown()


def test_cli(tmp_path):
    assert main(["check", "--mappings", os.path.join(S, "mappings.json"), "--keys", os.path.join(S, "keys.json")]) == 0
    assert main(["check", "--mappings", str(tmp_path / "x.json"), "--keys", os.path.join(S, "keys.json")]) == 2
