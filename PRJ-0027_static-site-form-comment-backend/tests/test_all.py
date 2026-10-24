import csv
import http.client
import io
import json
import os
import threading
from http.server import HTTPServer
import pytest
from form_backend import core, server
from form_backend.cli import main

CFGP = os.path.join(os.path.dirname(__file__), "..", "sample", "sites.json")
ORIGIN = "https://example.github.io"
TOK = "example-admin-token-change-me"


def be(rate=5, notifier=None):
    cfg = core.load_config(CFGP); cfg["rate_per_min"] = rate
    t = [1_900_000_000.0]
    b = core.Backend(cfg, core.connect(), lambda: t[0], notifier); b.t = t
    return b


GOOD = {"name": "가", "email": "a@b.com", "message": "안녕하세요"}


def test_form_ok_and_validation():
    b = be(); assert b.submit_form("blog", "contact", ORIGIN, "1.1.1.1", GOOD) == {"ok": True}
    assert b.db.execute("select count(*) from submissions").fetchone()[0] == 1
    for body, key in [({"name": "가"}, "email"), ({**GOOD, "email": "x"}, "email"), ({**GOOD, "message": "x" * 2001}, "message"), ({**GOOD, "name": 5}, "name")]:
        with pytest.raises(core.BackendError) as e: b.submit_form("blog", "contact", ORIGIN, "1.1.1.1", body)
        assert e.value.code == 422 and key in json.loads(str(e.value))


def test_origin_site_form_checks():
    b = be()
    with pytest.raises(core.BackendError) as e: b.submit_form("blog", "contact", "https://evil.com", "1", GOOD); assert e.value.code == 403
    with pytest.raises(core.BackendError) as e: b.submit_form("nope", "contact", ORIGIN, "1", GOOD)
    assert e.value.code == 404
    with pytest.raises(core.BackendError) as e: b.submit_form("blog", "x", ORIGIN, "1", GOOD)
    assert e.value.code == 404
    assert b.cors_headers("blog", ORIGIN) == {"Access-Control-Allow-Origin": ORIGIN} and b.cors_headers("blog", "https://evil.com") == {}


def test_honeypot_silently_dropped():
    b = be(); assert b.submit_form("blog", "contact", ORIGIN, "1", {**GOOD, "_gotcha": "bot"}) == {"ok": True}
    assert b.db.execute("select count(*) from submissions").fetchone()[0] == 0


def test_rate_limit_window_and_per_ip():
    b = be(rate=2)
    for _ in range(2): b.submit_form("blog", "contact", ORIGIN, "1", GOOD)
    with pytest.raises(core.BackendError) as e: b.submit_form("blog", "contact", ORIGIN, "1", GOOD)
    assert e.value.code == 429
    b.submit_form("blog", "contact", ORIGIN, "2", GOOD)                  # 다른 IP는 영향 없음
    b.t[0] += 61; b.submit_form("blog", "contact", ORIGIN, "1", GOOD)


def test_notifier_failure_does_not_lose_submission():
    def boom(*a): raise RuntimeError("mail down")
    b = be(notifier=boom); b.submit_form("blog", "contact", ORIGIN, "1", GOOD)
    assert b.db.execute("select count(*) from submissions").fetchone()[0] == 1


def test_comment_moderation_flow():
    b = be()
    assert b.post_comment("blog", ORIGIN, "1", {"page": "/p1", "name": "가", "text": "<script>alert(1)</script>"})["status"] == "pending"
    assert b.list_comments("blog", ORIGIN, "/p1")["comments"] == []       # 승인 전엔 안 보임
    pend = b.admin_pending(TOK)["pending"]; assert len(pend) == 1
    b.admin_moderate(TOK, pend[0]["id"], "approve")
    c = b.list_comments("blog", ORIGIN, "/p1")["comments"]
    assert c[0]["text"] == "<script>alert(1)</script>"                    # 원문 그대로(JSON). 화면에선 textContent로 넣을 것
    with pytest.raises(core.BackendError, match="대기 댓글"): b.admin_moderate(TOK, pend[0]["id"], "reject")
    for body in ({"page": "", "name": "a", "text": "b"}, {"page": "/p", "name": "a", "text": "x" * 1001}):
        with pytest.raises(core.BackendError) as e: b.post_comment("blog", ORIGIN, "1", body)
        assert e.value.code == 422


def test_admin_auth_and_export_formula_guard():
    b = be()
    for fn in (lambda: b.admin_pending("bad"), lambda: b.admin_pending(""), lambda: b.admin_export("x", "blog", "contact")):
        with pytest.raises(core.BackendError) as e: fn()
        assert e.value.code == 401
    b.submit_form("blog", "contact", ORIGIN, "1", {**GOOD, "message": "=HYPERLINK(1)"})
    rows = list(csv.reader(io.StringIO(b.admin_export(TOK, "blog", "contact"))))
    assert rows[0] == ["_ts", "email", "message", "name"] and rows[1][2].startswith("'=")


def test_config_errors(tmp_path):
    def w(c): p = tmp_path / "c.json"; p.write_text(json.dumps(c)); return str(p)
    base = json.load(open(CFGP, encoding="utf-8"))
    for c, msg in [({**base, "admin_token": "short"}, "16자"), ({**base, "sites": {}}, "sites"),
                   ({**base, "sites": {"a": {"origins": ["*"]}}}, "모두 허용"), ({**base, "sites": {"a": {}}}, "origins")]:
        with pytest.raises(core.BackendError, match=msg): core.load_config(w(c))


def test_http_end_to_end():
    b = be(); httpd = HTTPServer(("127.0.0.1", 0), server.make_handler(b)); port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    def call(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port)
        c.request(method, path, None if body is None else json.dumps(body), {"Origin": ORIGIN, **(headers or {})})
        r = c.getresponse(); return r.status, dict(r.getheaders()), r.read().decode()
    try:
        st, h, _ = call("POST", "/f/blog/contact", GOOD); assert st == 200 and h["Access-Control-Allow-Origin"] == ORIGIN
        st, _, body = call("POST", "/f/blog/contact", {"name": "x"}); assert st == 422 and "email" in json.loads(body)["error"]
        st, h, _ = call("POST", "/f/blog/contact", GOOD, {"Origin": "https://evil.com"}); assert st == 403 and "Access-Control-Allow-Origin" not in h
        st, h, _ = call("OPTIONS", "/f/blog/contact"); assert st == 204 and h["Access-Control-Allow-Origin"] == ORIGIN
        assert call("POST", "/c/blog", {"page": "/a", "name": "n", "text": "t"})[0] == 200
        assert call("GET", "/admin/pending")[0] == 401
        st, _, body = call("GET", "/admin/pending", headers={"X-Admin-Token": TOK}); cid = json.loads(body)["pending"][0]["id"]
        assert call("POST", f"/admin/approve/{cid}", headers={"X-Admin-Token": TOK})[0] == 200
        assert json.loads(call("GET", "/c/blog?page=/a")[2])["comments"][0]["name"] == "n"
        st, h, body = call("GET", "/admin/export/blog/contact", headers={"X-Admin-Token": TOK}); assert st == 200 and "text/csv" in h["Content-Type"]
        assert call("GET", "/nope")[0] == 404 and call("POST", "/admin/approve/abc", headers={"X-Admin-Token": TOK})[0] == 400
        c = http.client.HTTPConnection("127.0.0.1", port); c.request("POST", "/f/blog/contact", "x" * 30000, {"Origin": ORIGIN, "Content-Length": "30000"})
        assert c.getresponse().status == 413
    finally:
        httpd.shutdown()


def test_cli():
    assert main(["check", "--config", CFGP]) == 0 and main(["check", "--config", "/no/x.json"]) == 2
