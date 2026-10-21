"""링크 단축 + 클릭 기록 + 집계. 표준 라이브러리(SQLite)만 사용."""
import ipaddress
import re
import secrets
import sqlite3
from collections import Counter
from urllib.parse import urlparse

ALPHABET = "abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_RE = re.compile(r"^[A-Za-z0-9_-]{3,32}$")


class LinkError(ValueError):
    pass


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS links(code TEXT PRIMARY KEY, url TEXT NOT NULL, created TEXT NOT NULL)")
    db.execute("""CREATE TABLE IF NOT EXISTS clicks(id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT NOT NULL,
        ts TEXT NOT NULL, source TEXT NOT NULL, device TEXT NOT NULL, utm_source TEXT)""")
    return db


def validate_url(url):
    url = (url or "").strip()
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise LinkError("http:// 또는 https:// 주소만 줄일 수 있습니다")
    if not p.hostname:
        raise LinkError("주소에 도메인이 없습니다")
    try:
        ip = ipaddress.ip_address(p.hostname)
    except ValueError:
        ip = None
    if p.hostname == "localhost" or (ip and (ip.is_private or ip.is_loopback or ip.is_link_local)):
        raise LinkError("내부(사설) 주소는 줄일 수 없습니다")
    if len(url) > 2048:
        raise LinkError("주소가 너무 깁니다 (2048자 이하)")
    return url


def create(db, url, now, code=None):
    url = validate_url(url)
    if code is not None:
        if not CODE_RE.match(code):
            raise LinkError("코드는 영문·숫자·-·_ 3~32자")
    else:
        for _ in range(10):
            code = "".join(secrets.choice(ALPHABET) for _ in range(6))
            if not db.execute("SELECT 1 FROM links WHERE code=?", (code,)).fetchone():
                break
        else:
            raise LinkError("코드를 만들지 못했습니다")
    try:
        with db:
            db.execute("INSERT INTO links VALUES(?,?,?)", (code, url, now))
    except sqlite3.IntegrityError:
        raise LinkError("이미 있는 코드입니다")
    return code


def classify_source(referer):
    if not referer:
        return "직접 접속"
    host = (urlparse(referer).hostname or "").lower()
    table = [("naver", "네이버"), ("google", "구글"), ("kakao", "카카오"), ("instagram", "인스타그램"),
             ("facebook", "페이스북"), ("youtube", "유튜브"), ("t.co", "트위터"), ("twitter", "트위터"), ("x.com", "트위터")]
    for key, name in table:
        if key in host:
            return name
    return host or "기타"


def classify_device(ua):
    u = (ua or "").lower()
    if any(b in u for b in ("bot", "spider", "crawler")):
        return "봇"
    if "ipad" in u or "tablet" in u:
        return "태블릿"
    if "mobi" in u or "iphone" in u or "android" in u:
        return "모바일"
    return "PC" if u else "알 수 없음"


def resolve(db, code, now, referer=None, ua=None, utm_source=None):
    row = db.execute("SELECT url FROM links WHERE code=?", (code,)).fetchone()
    if not row:
        return None
    with db:
        db.execute("INSERT INTO clicks(code,ts,source,device,utm_source) VALUES(?,?,?,?,?)",
                   (code, now, classify_source(referer), classify_device(ua), utm_source))
    return row[0]


def stats(db, code, exclude_bots=True):
    if not db.execute("SELECT 1 FROM links WHERE code=?", (code,)).fetchone():
        raise LinkError("없는 코드입니다")
    rows = db.execute("SELECT ts,source,device,utm_source FROM clicks WHERE code=?", (code,)).fetchall()
    bots = sum(1 for r in rows if r[2] == "봇")
    if exclude_bots:
        rows = [r for r in rows if r[2] != "봇"]
    return {"total": len(rows), "bots_excluded": bots if exclude_bots else 0,
            "by_day": sorted(Counter(r[0][:10] for r in rows).items()),
            "by_source": Counter(r[1] for r in rows).most_common(),
            "by_device": Counter(r[2] for r in rows).most_common(),
            "by_utm": Counter(r[3] for r in rows if r[3]).most_common()}
