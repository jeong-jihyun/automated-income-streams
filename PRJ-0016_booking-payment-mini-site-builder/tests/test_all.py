import json
import os
import threading
import urllib.request
import urllib.error
from datetime import datetime
from http.server import HTTPServer
import pytest
from booking_site import config, engine, payment, site, server
from booking_site.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "shop.json")
NOW = datetime(2030, 1, 1, 9, 0)


@pytest.fixture
def env():
    cfg = config.load(SAMPLE)
    return cfg, engine.connect()


def test_slots(env):
    cfg, _ = env
    s = engine.slots_for(cfg, "2030-01-10")
    assert s[0] == "2030-01-10 10:00" and s[-1] == "2030-01-10 17:00" and len(s) == 8
    with pytest.raises(engine.BookingError): engine.slots_for(cfg, "01/10")


def test_double_booking_blocked(env):
    cfg, db = env
    engine.book(db, cfg, "2030-01-10 10:00", "basic", "가", NOW)
    with pytest.raises(engine.BookingError, match="이미 예약"): engine.book(db, cfg, "2030-01-10 10:00", "art", "나", NOW)
    assert "2030-01-10 10:00" not in engine.free_slots(db, cfg, "2030-01-10")


def test_double_booking_race_threads(env):
    """스레드마다 따로 DB 연결을 열어 같은 칸을 동시에 예약 → 한 명만 성공해야 한다."""
    cfg, _ = env
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), "t.db")
    engine.connect(path).close()
    results = []
    def go(i):
        conn = engine.connect(path)
        try: engine.book(conn, cfg, "2030-01-10 11:00", "basic", f"사람{i}", NOW); results.append("ok")
        except engine.BookingError: results.append("fail")
        finally: conn.close()
    ts = [threading.Thread(target=go, args=(i,)) for i in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert results.count("ok") == 1 and results.count("fail") == 7
    chk = engine.connect(path)
    assert chk.execute("select count(*) from bookings").fetchone()[0] == 1


def test_validation(env):
    cfg, db = env
    for slot, svc, name, msg in [("2030-01-10 10:30", "basic", "가", "예약할 수 없는"), ("2030-01-10 10:00", "x", "가", "없는 서비스"),
                                  ("2030-01-10 10:00", "basic", " ", "이름"), ("2029-12-31 10:00", "basic", "가", "지난")]:
        with pytest.raises(engine.BookingError, match=msg): engine.book(db, cfg, slot, svc, name, NOW)


def test_refund_tiers(env):
    cfg, _ = env
    slot = "2030-01-10 10:00"
    assert engine.refund_percent(cfg, slot, datetime(2030, 1, 8, 10, 0)) == 100   # 정확히 48시간 전
    assert engine.refund_percent(cfg, slot, datetime(2030, 1, 8, 10, 1)) == 50    # 47시간 59분 전
    assert engine.refund_percent(cfg, slot, datetime(2030, 1, 9, 10, 0)) == 50    # 24시간 전
    assert engine.refund_percent(cfg, slot, datetime(2030, 1, 9, 10, 1)) == 0
    assert engine.refund_percent(cfg, slot, datetime(2030, 1, 10, 12, 0)) == 0    # 이미 지남


def test_pay_and_cancel_flow(env):
    cfg, db = env
    bid = engine.book(db, cfg, "2030-01-10 10:00", "art", "가", NOW)
    with pytest.raises(engine.BookingError, match="시험용 카드"): payment.pay_test(db, bid, "1111 2222 3333 4444")
    assert payment.pay_test(db, bid, "4242 4242 4242 4242")["mode"] == "TEST"
    with pytest.raises(engine.BookingError, match="이미 결제"): payment.pay_test(db, bid, "4242424242424242")
    r = engine.cancel(db, cfg, bid, datetime(2030, 1, 9, 9, 0))
    assert r == {"percent": 50, "refund": 25000}
    with pytest.raises(engine.BookingError, match="이미 취소"): engine.cancel(db, cfg, bid, NOW)
    assert "2030-01-10 10:00" in engine.free_slots(db, cfg, "2030-01-10")           # 취소하면 다시 예약 가능
    engine.book(db, cfg, "2030-01-10 10:00", "basic", "나", NOW)


def test_cancel_unpaid_refunds_zero(env):
    cfg, db = env
    bid = engine.book(db, cfg, "2030-01-10 10:00", "basic", "가", NOW)
    assert engine.cancel(db, cfg, bid, NOW)["refund"] == 0
    with pytest.raises(engine.BookingError, match="찾을"): engine.cancel(db, cfg, 999, NOW)


def test_config_errors(tmp_path):
    def w(**ch):
        c = json.load(open(SAMPLE, encoding="utf-8")); c.update(ch)
        p = tmp_path / "c.json"; p.write_text(json.dumps(c), encoding="utf-8"); return str(p)
    for kw, msg in [({"open": "9:00"}, "HH:MM"), ({"open": "19:00"}, "늦어야"), ({"slot_minutes": 0}, "slot_minutes"),
                    ({"refund_policy": [{"hours_before": 24, "percent": 100}]}, "0 단계"), ({"services": []}, "서비스가 하나도")]:
        with pytest.raises(config.ConfigError, match=msg): config.load(w(**kw))
    with pytest.raises(config.ConfigError, match="없습니다"): config.load(str(tmp_path / "none.json"))
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(config.ConfigError, match="JSON"): config.load(str(tmp_path / "bad.json"))


def test_page_mobile_and_escape(env):
    cfg, _ = env
    cfg = dict(cfg, shop_name="<b>샵</b>")
    h = site.build_page(cfg)
    assert 'name="viewport"' in h and "&lt;b&gt;샵" in h and "시험용" in h and "100% 환불" in h


def test_http_server_end_to_end(env):
    cfg, db = env
    httpd = HTTPServer(("127.0.0.1", 0), server.make_handler(cfg, db))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"
    def call(path, body=None):
        req = urllib.request.Request(base + path, data=None if body is None else json.dumps(body).encode(), method="POST" if body is not None else "GET")
        try:
            with urllib.request.urlopen(req) as r: return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
    try:
        assert "text/html" in urllib.request.urlopen(base + "/").headers["Content-Type"]
        assert len(call("/api/slots?date=2099-01-10")[1]["slots"]) == 8
        code, r = call("/api/book", {"slot": "2099-01-10 10:00", "service": "basic", "name": "가"})
        assert code == 201
        assert call("/api/book", {"slot": "2099-01-10 10:00", "service": "basic", "name": "나"})[0] == 400
        assert call("/api/pay", {"id": r["id"], "card": "4242424242424242"})[1]["mode"] == "TEST"
        assert call("/api/cancel", {"id": r["id"]})[1]["percent"] == 100
        assert call("/api/slots?date=bad")[0] == 400 and call("/nope")[0] == 404
        assert call("/api/cancel", {"id": 999})[0] == 404
    finally:
        httpd.shutdown()


def test_cli(tmp_path):
    assert main(["check", "--config", SAMPLE]) == 0
    assert main(["build", "--config", SAMPLE, "--out", str(tmp_path)]) == 0 and (tmp_path / "index.html").exists()
    assert main(["check", "--config", str(tmp_path / "x.json")]) == 2
