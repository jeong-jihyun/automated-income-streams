"""서버 없는 정적 사이트(블로그 등)에 붙이는 문의 폼·댓글 백엔드. 허용 도메인(CORS), 스팸 함정 칸, 호출 제한, 댓글 승인제.
표준 라이브러리(SQLite, http.server)만 사용. 메일 알림은 notifier 함수를 바깥에서 넣는다(실제 발송 없음)."""
import hmac
import json
import re
import sqlite3
from collections import defaultdict

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BackendError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg); self.code = code


def load_config(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise BackendError(500, f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise BackendError(500, f"JSON 형식 오류: {e}")
    if len(cfg.get("admin_token", "")) < 16:
        raise BackendError(500, "admin_token은 16자 이상이어야 합니다")
    if not cfg.get("sites"):
        raise BackendError(500, "sites가 비었습니다")
    for sid, s in cfg["sites"].items():
        if not s.get("origins"):
            raise BackendError(500, f"{sid}: origins(허용 주소)가 필요합니다")
        if "*" in s["origins"]:
            raise BackendError(500, f"{sid}: origins에 '*'(모두 허용)는 쓸 수 없습니다")
    cfg.setdefault("rate_per_min", 5)
    return cfg


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS submissions(id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT, form TEXT, data TEXT, ts TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS comments(id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT, page TEXT, name TEXT, text TEXT, status TEXT, ts TEXT)")
    return db


class Backend:
    def __init__(self, cfg, db, clock, notifier=None):
        self.cfg, self.db, self.clock, self.notifier = cfg, db, clock, notifier
        self.hits = defaultdict(list)

    def _site(self, site_id, origin):
        s = self.cfg["sites"].get(site_id)
        if not s:
            raise BackendError(404, "없는 사이트입니다")
        if origin not in s["origins"]:
            raise BackendError(403, "허용되지 않은 주소에서 보낸 요청입니다")
        return s

    def _limit(self, ip, site_id):
        key, now = (ip, site_id), self.clock()
        self.hits[key] = [t for t in self.hits[key] if now - t < 60]
        if len(self.hits[key]) >= self.cfg["rate_per_min"]:
            raise BackendError(429, "잠시 후 다시 시도하세요")
        self.hits[key].append(now)

    def cors_headers(self, site_id, origin):
        s = self.cfg["sites"].get(site_id)
        return {"Access-Control-Allow-Origin": origin} if s and origin in s["origins"] else {}

    def submit_form(self, site_id, form_id, origin, ip, body):
        s = self._site(site_id, origin); self._limit(ip, site_id)
        form = s.get("forms", {}).get(form_id)
        if not form:
            raise BackendError(404, "없는 폼입니다")
        if body.get("_gotcha"):                                  # 사람은 보지 못하는 함정 칸 — 채워져 있으면 봇
            return {"ok": True}                                   # 봇이 눈치채지 못하게 성공처럼 응답하고 저장은 하지 않는다
        data, errs = {}, {}
        for name, rule in form["fields"].items():
            v = body.get(name); v = v.strip() if isinstance(v, str) else v
            if not v:
                if rule.get("required"): errs[name] = "필수 항목입니다"
                continue
            if not isinstance(v, str): errs[name] = "글자여야 합니다"; continue
            if len(v) > rule.get("max", 500): errs[name] = f"{rule.get('max', 500)}자 이하여야 합니다"; continue
            if rule.get("type") == "email" and not EMAIL.match(v): errs[name] = "이메일 형식이 아닙니다"; continue
            data[name] = v
        if errs:
            raise BackendError(422, json.dumps(errs, ensure_ascii=False))
        with self.db:
            self.db.execute("INSERT INTO submissions(site,form,data,ts) VALUES(?,?,?,?)", (site_id, form_id, json.dumps(data, ensure_ascii=False), self.clock_str()))
        if self.notifier:
            try: self.notifier(site_id, form_id, data)
            except Exception: pass
        return {"ok": True}

    def clock_str(self):
        import datetime
        return datetime.datetime.fromtimestamp(self.clock()).strftime("%Y-%m-%d %H:%M:%S")

    def post_comment(self, site_id, origin, ip, body):
        s = self._site(site_id, origin); self._limit(ip, site_id)
        cfg = s.get("comments")
        if not cfg:
            raise BackendError(404, "댓글 기능이 꺼져 있습니다")
        if body.get("_gotcha"):
            return {"ok": True, "status": "pending"}
        page, name, text = (str(body.get(k, "")).strip() for k in ("page", "name", "text"))
        if not page or not name or not text:
            raise BackendError(422, "page, name, text가 필요합니다")
        if len(text) > cfg.get("max_len", 1000) or len(name) > 50 or len(page) > 300:
            raise BackendError(422, "글이 너무 깁니다")
        status = "pending" if cfg.get("require_approval", True) else "approved"
        with self.db:
            self.db.execute("INSERT INTO comments(site,page,name,text,status,ts) VALUES(?,?,?,?,?,?)", (site_id, page, name, text, status, self.clock_str()))
        return {"ok": True, "status": status}

    def list_comments(self, site_id, origin, page):
        self._site(site_id, origin)
        rows = self.db.execute("SELECT name,text,ts FROM comments WHERE site=? AND page=? AND status='approved' ORDER BY id", (site_id, page)).fetchall()
        return {"comments": [{"name": n, "text": t, "ts": ts} for n, t, ts in rows]}      # 글자는 그대로 주고, 화면에 넣을 때 textContent로 넣는다

    def _admin(self, token):
        if not hmac.compare_digest(token or "", self.cfg["admin_token"]):
            raise BackendError(401, "관리자 토큰이 올바르지 않습니다")

    def admin_pending(self, token):
        self._admin(token)
        return {"pending": [dict(zip(("id", "site", "page", "name", "text"), r)) for r in self.db.execute("SELECT id,site,page,name,text FROM comments WHERE status='pending' ORDER BY id")]}

    def admin_moderate(self, token, cid, action):
        self._admin(token)
        if action not in ("approve", "reject"):
            raise BackendError(400, "action은 approve 또는 reject")
        with self.db:
            cur = self.db.execute("UPDATE comments SET status=? WHERE id=? AND status='pending'", ("approved" if action == "approve" else "rejected", cid))
        if cur.rowcount == 0:
            raise BackendError(404, "처리할 대기 댓글이 없습니다")
        return {"ok": True}

    def admin_export(self, token, site_id, form_id):
        self._admin(token)
        import csv, io
        rows = [json.loads(r[0]) | {"_ts": r[1]} for r in self.db.execute("SELECT data,ts FROM submissions WHERE site=? AND form=? ORDER BY id", (site_id, form_id))]
        cols = sorted({k for r in rows for k in r})
        buf = io.StringIO(); w = csv.writer(buf); w.writerow(cols)
        for r in rows:
            w.writerow([("'" + str(r.get(c, "")) if str(r.get(c, ""))[:1] in "=+@" and r.get(c) else r.get(c, "")) for c in cols])
        return buf.getvalue()
