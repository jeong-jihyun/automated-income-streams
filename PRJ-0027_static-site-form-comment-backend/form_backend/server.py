import json
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from .core import BackendError

MAX_BODY = 20_000


def make_handler(be):
    class H(BaseHTTPRequestHandler):
        def _send(self, code, obj, site=None, raw=None, ctype="application/json; charset=utf-8"):
            data = raw.encode("utf-8") if raw is not None else json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(data)))
            if site: [self.send_header(k, v) for k, v in be.cors_headers(site, self.headers.get("Origin", "")).items()]
            self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers(); self.wfile.write(data)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if n > MAX_BODY: raise BackendError(413, "요청이 너무 큽니다")
            try: return json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError: raise BackendError(400, "JSON 형식 오류")

        def do_OPTIONS(self):
            parts = urlparse(self.path).path.strip("/").split("/")
            site = parts[1] if len(parts) > 1 else None
            self.send_response(204)
            for k, v in be.cors_headers(site, self.headers.get("Origin", "")).items(): self.send_header(k, v)
            self.send_header("Access-Control-Allow-Methods", "GET, POST"); self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", "0"); self.end_headers()

        def _route(self, method):
            u = urlparse(self.path); p = u.path.strip("/").split("/"); origin = self.headers.get("Origin", ""); ip = self.client_address[0]
            tok = self.headers.get("X-Admin-Token", "")
            site = p[1] if len(p) > 1 else None
            try:
                if method == "POST" and p[0] == "f" and len(p) == 3:
                    return self._send(200, be.submit_form(p[1], p[2], origin, ip, self._body()), p[1])
                if method == "POST" and p[0] == "c" and len(p) == 2:
                    return self._send(200, be.post_comment(p[1], origin, ip, self._body()), p[1])
                if method == "GET" and p[0] == "c" and len(p) == 2:
                    return self._send(200, be.list_comments(p[1], origin, parse_qs(u.query).get("page", [""])[0]), p[1])
                if p[0] == "admin":
                    if method == "GET" and p[1:] == ["pending"]: return self._send(200, be.admin_pending(tok))
                    if method == "POST" and len(p) == 3 and p[1] in ("approve", "reject"): return self._send(200, be.admin_moderate(tok, int(p[2]), p[1]))
                    if method == "GET" and len(p) == 4 and p[1] == "export": return self._send(200, None, raw=be.admin_export(tok, p[2], p[3]), ctype="text/csv; charset=utf-8")
                raise BackendError(404, "없는 주소")
            except BackendError as e:
                body = {"error": json.loads(str(e))} if e.code == 422 and str(e).startswith("{") else {"error": str(e)}
                self._send(e.code, body, site)
            except (ValueError, IndexError):
                self._send(400, {"error": "잘못된 요청"})

        def do_GET(self): self._route("GET")
        def do_POST(self): self._route("POST")
        def log_message(self, *a): pass
    return H


def serve(be, port):
    HTTPServer(("127.0.0.1", port), make_handler(be)).serve_forever()
