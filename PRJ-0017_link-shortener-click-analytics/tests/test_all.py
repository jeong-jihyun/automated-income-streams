import http.client
import json
import threading
from http.server import HTTPServer
import pytest
from link_short import core, server
from link_short.cli import main

T = "2030-01-01 10:00:00"


@pytest.fixture
def db():
    return core.connect()


@pytest.mark.parametrize("bad", ["javascript:alert(1)", "ftp://a.com", "http://", "http://127.0.0.1/x", "http://192.168.0.5", "http://localhost:3000", "abc", "", "https://a.com/" + "x" * 2100])
def test_rejects_bad_urls(db, bad):
    with pytest.raises(core.LinkError): core.create(db, bad, T)


def test_create_and_custom_code(db):
    c = core.create(db, "https://example.com/a?b=1", T)
    assert len(c) == 6 and core.resolve(db, c, T) == "https://example.com/a?b=1"
    assert core.create(db, "https://example.com", T, "my-link") == "my-link"
    with pytest.raises(core.LinkError, match="이미"): core.create(db, "https://example.com", T, "my-link")
    with pytest.raises(core.LinkError, match="코드는"): core.create(db, "https://example.com", T, "a b")
    assert core.resolve(db, "none", T) is None


def test_classifiers():
    assert core.classify_source(None) == "직접 접속"
    assert core.classify_source("https://search.naver.com/x") == "네이버"
    assert core.classify_source("https://l.instagram.com/") == "인스타그램"
    assert core.classify_source("https://blog.example.org/p") == "blog.example.org"
    assert core.classify_device("Mozilla/5.0 (iPhone; CPU) Mobile") == "모바일"
    assert core.classify_device("Googlebot/2.1") == "봇"
    assert core.classify_device("Mozilla/5.0 (Windows NT 10.0)") == "PC"
    assert core.classify_device(None) == "알 수 없음"


def test_stats_counts_and_bot_exclusion(db):
    c = core.create(db, "https://example.com", T)
    core.resolve(db, c, "2030-01-01 10:00:00", "https://search.naver.com/", "Mozilla Mobile", "ad")
    core.resolve(db, c, "2030-01-01 11:00:00", None, "Windows", None)
    core.resolve(db, c, "2030-01-02 09:00:00", "https://www.google.com/", "Mozilla Mobile", "ad")
    core.resolve(db, c, "2030-01-02 09:01:00", None, "Googlebot", None)
    s = core.stats(db, c)
    assert s["total"] == 3 and s["bots_excluded"] == 1
    assert s["by_day"] == [("2030-01-01", 2), ("2030-01-02", 1)]
    assert dict(s["by_source"]) == {"네이버": 1, "직접 접속": 1, "구글": 1}
    assert dict(s["by_device"]) == {"모바일": 2, "PC": 1} and s["by_utm"] == [("ad", 2)]
    assert core.stats(db, c, exclude_bots=False)["total"] == 4
    with pytest.raises(core.LinkError): core.stats(db, "zzz")


def test_http_redirect_and_api(db):
    httpd = HTTPServer(("127.0.0.1", 0), server.make_handler(db, clock=lambda: T))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    def req(method, path, body=None, headers=None):
        c = http.client.HTTPConnection("127.0.0.1", port)
        c.request(method, path, None if body is None else json.dumps(body), headers or {})
        r = c.getresponse(); data = r.read(); return r, data
    try:
        r, d = req("POST", "/api/links", {"url": "https://example.com/landing", "code": "abc123"})
        assert r.status == 201
        assert req("POST", "/api/links", {"url": "https://example.com", "code": "abc123"})[0].status == 409
        assert req("POST", "/api/links", {"url": "javascript:x"})[0].status == 400
        r, _ = req("GET", "/abc123?utm_source=news", headers={"Referer": "https://www.google.com/", "User-Agent": "Mozilla Mobile"})
        assert r.status == 302 and r.getheader("Location") == "https://example.com/landing"
        r, d = req("GET", "/api/stats/abc123")
        st = json.loads(d)
        assert r.status == 200 and st["total"] == 1 and st["by_utm"] == [["news", 1]]
        assert req("GET", "/nope")[0].status == 404 and req("GET", "/api/stats/nope")[0].status == 404
        assert req("GET", "/")[0].status == 404
    finally:
        httpd.shutdown()


def test_cli(tmp_path, capsys):
    f = str(tmp_path / "l.db")
    assert main(["--db", f, "add", "https://example.com", "--code", "hello"]) == 0
    assert main(["--db", f, "add", "ftp://x.com"]) == 2
    assert main(["--db", f, "stats", "hello"]) == 0 and "클릭 0회" in capsys.readouterr().out
    assert main(["--db", f, "stats", "zzz"]) == 2
