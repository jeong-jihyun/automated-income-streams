import json
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import pytest
from uptime_monitor import core
from uptime_monitor.cli import main


class H(BaseHTTPRequestHandler):
    mode = "ok"
    hooks = []
    def do_GET(self):
        if self.path == "/slow": time.sleep(0.4)
        code = 500 if self.path == "/err" else 200
        body = b"hello Example page" if self.path != "/nokw" else b"nothing"
        self.send_response(code); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_POST(self):
        H.hooks.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers()
    def log_message(self, *a): pass


@pytest.fixture(scope="module")
def srv():
    httpd = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def test_check_ok_err_keyword_slow_down(srv):
    assert core.check_site({"url": srv + "/"}, 2, 2000)["ok"]
    r = core.check_site({"url": srv + "/err"}, 2, 2000); assert not r["ok"] and r["status"] == 500 and "500" in r["reason"]
    assert core.check_site({"url": srv + "/", "keyword": "Example"}, 2, 2000)["ok"]
    r = core.check_site({"url": srv + "/nokw", "keyword": "Example"}, 2, 2000); assert not r["ok"] and "확인 문구" in r["reason"]
    r = core.check_site({"url": srv + "/slow"}, 2, 100); assert r["ok"] and r["reason"] == "느림" and r["ms"] >= 300
    r = core.check_site({"url": "http://127.0.0.1:9/"}, 1, 100); assert not r["ok"] and r["status"] is None and "접속 실패" in r["reason"]
    r = core.check_site({"url": srv + "/slow"}, 0.1, 100); assert not r["ok"]   # 시간 초과


def test_state_machine_alerts_only_on_transitions():
    db = core.connect()
    bad = {"ok": False, "status": 500, "ms": 5, "reason": "HTTP 500"}; good = {"ok": True, "status": 200, "ms": 5, "reason": ""}
    alerts = [core.record(db, "s", f"t{i}", r, 2) for i, r in enumerate([good, bad, bad, bad, good, good, bad, good])]
    assert alerts[0] is None and alerts[1] is None                    # 1번 실패는 알리지 않음
    assert "장애" in alerts[2] and alerts[3] is None                  # 2번 연속 → 한 번만 알림
    assert "복구" in alerts[4] and "t2" in alerts[4]                   # 복구 + 장애 시작 시각
    assert alerts[5] is None and alerts[6] is None and alerts[7] is None  # 한 번 실패 후 회복은 알림 없음
    assert core.uptime_percent(db, "s") == round(100 * 4 / 8, 2)
    assert core.uptime_percent(db, "none") is None


def test_status_page(srv):
    db = core.connect(); cfg = {"sites": [{"name": "<a>", "url": srv}, {"name": "b", "url": srv}]}
    core.record(db, "<a>", "t", {"ok": False, "status": 500, "ms": 1, "reason": "x"}, 1)
    core.record(db, "b", "t", {"ok": True, "status": 200, "ms": 12, "reason": ""}, 1)
    h = core.status_page(db, cfg, "2030-01-01")
    assert "&lt;a&gt;" in h and "장애" in h and "정상" in h and "응답 12ms" in h
    assert "아직 점검 전" in core.status_page(core.connect(), cfg, "x")


def test_webhook_and_run_once(srv):
    H.hooks.clear()
    db = core.connect(); cfg = {"sites": [{"name": "dead", "url": "http://127.0.0.1:9/"}], "timeout_sec": 1, "fail_threshold": 1, "slow_ms": 100}
    sent = []
    core.run_once(db, cfg, "t", lambda t: (sent.append(t), core.send_webhook(srv + "/hook", t)))
    assert len(sent) == 1 and H.hooks and "접속 장애" in H.hooks[0]["text"]


def test_config_errors(tmp_path):
    def w(c): p = tmp_path / "c.json"; p.write_text(json.dumps(c), encoding="utf-8"); return str(p)
    for c, msg in [({"sites": []}, "비었"), ({"sites": [{"name": "a", "url": "ftp://x"}]}, "http"),
                   ({"sites": [{"name": "a", "url": "http://x"}, {"name": "a", "url": "http://y"}]}, "중복"),
                   ({"sites": [{"name": "a", "url": "http://x"}], "fail_threshold": 0}, "fail_threshold")]:
        with pytest.raises(core.MonitorError, match=msg): core.load_config(w(c))
    with pytest.raises(core.MonitorError): core.load_config(str(tmp_path / "none.json"))


def test_cli_once(srv, tmp_path, capsys):
    cfgp = tmp_path / "c.json"; cfgp.write_text(json.dumps({"sites": [{"name": "ok", "url": srv + "/"}]}), encoding="utf-8")
    page = tmp_path / "s.html"
    assert main(["--config", str(cfgp), "--db", str(tmp_path / "m.db"), "--page", str(page)]) == 0
    assert "정상" in page.read_text(encoding="utf-8")
    assert main(["--config", str(tmp_path / "x.json")]) == 2
