import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from .gateway import GatewayError


def make_handler(gw):
    class H(BaseHTTPRequestHandler):
        def _json(self, code, obj):
            d = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(d))); self.end_headers(); self.wfile.write(d)

        def do_GET(self):
            u = urlparse(self.path)
            key = self.headers.get("X-API-Key", "")
            try:
                if u.path == "/v1/orders":
                    ch = parse_qs(u.query).get("channel")
                    return self._json(200, gw.orders(key, ch[0].split(",") if ch else None))
                if u.path == "/v1/usage":
                    gw._auth(key)
                    return self._json(200, {"calls": gw.usage[key]})
            except GatewayError as e:
                return self._json(e.code, {"error": str(e)})
            self._json(404, {"error": "없는 주소"})

        def log_message(self, *a): pass
    return H


def serve(gw, port):
    HTTPServer(("127.0.0.1", port), make_handler(gw)).serve_forever()
