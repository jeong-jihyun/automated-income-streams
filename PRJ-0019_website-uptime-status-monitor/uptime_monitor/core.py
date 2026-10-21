"""사이트 점검, 연속 실패 판정, 기록, 가동률, 상태 페이지. 표준 라이브러리만 사용."""
import html
import json
import sqlite3
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse


class MonitorError(ValueError):
    pass


def load_config(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise MonitorError(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise MonitorError(f"JSON 형식 오류: {e}")
    errs = []
    if not cfg.get("sites"):
        errs.append("sites가 비었습니다")
    names = [s.get("name") for s in cfg.get("sites", [])]
    if len(set(names)) != len(names) or not all(names):
        errs.append("사이트 이름이 비었거나 중복입니다")
    for s in cfg.get("sites", []):
        if urlparse(s.get("url", "")).scheme not in ("http", "https"):
            errs.append(f"{s.get('name')}: url은 http(s)여야 합니다")
    cfg.setdefault("timeout_sec", 5); cfg.setdefault("fail_threshold", 2); cfg.setdefault("slow_ms", 2000)
    if cfg["timeout_sec"] <= 0 or cfg["fail_threshold"] < 1:
        errs.append("timeout_sec는 0보다 크고 fail_threshold는 1 이상이어야 합니다")
    if errs:
        raise MonitorError("; ".join(errs))
    return cfg


def check_site(site, timeout, slow_ms):
    """한 번 점검. 결과: {ok, status, ms, reason}"""
    t0 = time.monotonic()
    try:
        req = urllib.request.Request(site["url"], headers={"User-Agent": "uptime-monitor/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read(200_000).decode("utf-8", "replace")
            status = r.status
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "ms": int((time.monotonic() - t0) * 1000), "reason": f"HTTP {e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "status": None, "ms": int((time.monotonic() - t0) * 1000), "reason": f"접속 실패: {getattr(e, 'reason', e)}"}
    ms = int((time.monotonic() - t0) * 1000)
    if site.get("keyword") and site["keyword"] not in body:
        return {"ok": False, "status": status, "ms": ms, "reason": "페이지에 확인 문구가 없습니다"}
    if ms > slow_ms:
        return {"ok": True, "status": status, "ms": ms, "reason": "느림"}
    return {"ok": True, "status": status, "ms": ms, "reason": ""}


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False)
    db.execute("CREATE TABLE IF NOT EXISTS checks(id INTEGER PRIMARY KEY AUTOINCREMENT, site TEXT, ts TEXT, ok INTEGER, status INTEGER, ms INTEGER, reason TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS state(site TEXT PRIMARY KEY, down INTEGER NOT NULL DEFAULT 0, fails INTEGER NOT NULL DEFAULT 0, since TEXT)")
    return db


def record(db, site, ts, res, threshold):
    """점검 결과를 저장하고 상태가 바뀌면 알림 문구를 돌려준다 (장애 시작 / 복구 때만)."""
    with db:
        db.execute("INSERT INTO checks(site,ts,ok,status,ms,reason) VALUES(?,?,?,?,?,?)",
                   (site, ts, int(res["ok"]), res["status"], res["ms"], res["reason"]))
        row = db.execute("SELECT down,fails,since FROM state WHERE site=?", (site,)).fetchone() or (0, 0, None)
        down, fails, since = row
        alert = None
        if res["ok"]:
            if down:
                alert = f"✅ [{site}] 복구되었습니다 (장애 시작 {since})"
            down, fails, since = 0, 0, None
        else:
            fails += 1
            if not down and fails >= threshold:
                down, since = 1, ts
                alert = f"🔴 [{site}] 접속 장애: {res['reason']} (연속 {fails}회 실패)"
        db.execute("INSERT OR REPLACE INTO state VALUES(?,?,?,?)", (site, down, fails, since))
    return alert


def uptime_percent(db, site):
    n, ok = db.execute("SELECT COUNT(*), COALESCE(SUM(ok),0) FROM checks WHERE site=?", (site,)).fetchone()
    return None if n == 0 else round(100 * ok / n, 2)


def status_page(db, cfg, now):
    e = html.escape
    rows = []
    for s in cfg["sites"]:
        st = db.execute("SELECT down FROM state WHERE site=?", (s["name"],)).fetchone()
        last = db.execute("SELECT ts,ms,reason FROM checks WHERE site=? ORDER BY id DESC LIMIT 1", (s["name"],)).fetchone()
        if not last:
            label, color = "아직 점검 전", "#888"
        elif st and st[0]:
            label, color = "장애", "#C0392B"
        else:
            label, color = "정상", "#1E8449"
        up = uptime_percent(db, s["name"])
        rows.append(f"<li><b>{e(s['name'])}</b> — <span style='color:{color}'>{label}</span> · 가동률 {'-' if up is None else str(up) + '%'}"
                    + (f" · 응답 {last[1]}ms" if last else "") + "</li>")
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>서비스 상태</title></head><body style='font-family:sans-serif;max-width:480px;margin:auto;padding:16px'>"
            f"<h1>서비스 상태</h1><ul>{''.join(rows)}</ul><p><small>마지막 갱신 {e(now)}</small></p></body></html>")


def send_webhook(url, text, timeout=5):
    req = urllib.request.Request(url, data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status


def run_once(db, cfg, now, notify=print):
    out = []
    for s in cfg["sites"]:
        res = check_site(s, cfg["timeout_sec"], cfg["slow_ms"])
        alert = record(db, s["name"], now, res, cfg["fail_threshold"])
        out.append((s["name"], res, alert))
        if alert:
            notify(alert)
    return out
