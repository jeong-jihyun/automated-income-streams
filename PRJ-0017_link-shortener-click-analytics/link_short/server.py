import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from . import core


def make_handler(db, clock=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")):
    class H(BaseHTTPRequestHandler):
        def _json(self, code, obj):
            d = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path.startswith("/api/stats/"):
                try:
                    return self._json(200, core.stats(db, u.path.split("/")[-1]))
                except core.LinkError as e:
                    return self._json(404, {"error": str(e)})
            code = u.path.strip("/")
            target = core.resolve(db, code, clock(), self.headers.get("Referer"), self.headers.get("User-Agent"),
                                  parse_qs(u.query).get("utm_source", [None])[0]) if code else None
            if target:
                self.send_response(302); self.send_header("Location", target); self.send_header("Content-Length", "0"); self.end_headers()
            else:
                self._json(404, {"error": "없는 링크입니다"})

        def do_POST(self):
            if self.path != "/api/links":
                return self._json(404, {"error": "없는 주소"})
            try:
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                code = core.create(db, body.get("url", ""), clock(), body.get("code"))
                return self._json(201, {"code": code})
            except json.JSONDecodeError:
                return self._json(400, {"error": "JSON 형식 오류"})
            except core.LinkError as e:
                return self._json(409 if "이미" in str(e) else 400, {"error": str(e)})

        def log_message(self, *a): pass
    return H


def serve(db, port):
    HTTPServer(("127.0.0.1", port), make_handler(db)).serve_forever()
