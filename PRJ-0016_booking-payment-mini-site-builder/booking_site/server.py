"""시험용 서버(http.server). 실제 운영용이 아닙니다."""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from . import engine, payment, site


def make_handler(cfg, db):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

        def _json(self, code, obj): self._send(code, json.dumps(obj, ensure_ascii=False))

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/":
                return self._send(200, site.build_page(cfg), "text/html; charset=utf-8")
            if u.path == "/api/slots":
                try:
                    return self._json(200, {"slots": engine.free_slots(db, cfg, parse_qs(u.query).get("date", [""])[0])})
                except engine.BookingError as e:
                    return self._json(400, {"error": str(e)})
            self._json(404, {"error": "없는 주소"})

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return self._json(400, {"error": "JSON 형식 오류"})
            try:
                if self.path == "/api/book":
                    bid = engine.book(db, cfg, body.get("slot", ""), body.get("service", ""), body.get("name", ""))
                    return self._json(201, {"id": bid})
                if self.path == "/api/pay":
                    return self._json(200, payment.pay_test(db, int(body.get("id", 0)), body.get("card", "")))
                if self.path == "/api/cancel":
                    return self._json(200, engine.cancel(db, cfg, int(body.get("id", 0))))
            except (engine.BookingError, ValueError) as e:
                return self._json(400 if not isinstance(e, engine.BookingError) or "찾을" not in str(e) else 404, {"error": str(e)})
            self._json(404, {"error": "없는 주소"})

        def log_message(self, *a): pass
    return H


def serve(cfg, db, port=8000):
    HTTPServer(("127.0.0.1", port), make_handler(cfg, db)).serve_forever()
