"""SQLite 저장소: 반, 보호자(아이 이름·사진 동의), 알림장, 전달 기록(읽음 확인용 개인별 토큰)."""
import secrets
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS classes(id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL);
CREATE TABLE IF NOT EXISTS guardians(id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL REFERENCES classes(id),
  child TEXT NOT NULL, name TEXT NOT NULL, phone TEXT NOT NULL, photo_ok INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
  UNIQUE(class_id, child, phone));
CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY, class_id INTEGER NOT NULL, title TEXT NOT NULL, body TEXT NOT NULL,
  photos TEXT NOT NULL DEFAULT '[]', created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS deliveries(id INTEGER PRIMARY KEY, notice_id INTEGER NOT NULL, guardian_id INTEGER NOT NULL,
  token TEXT UNIQUE NOT NULL, status TEXT NOT NULL, read_at TEXT, UNIQUE(notice_id, guardian_id));
"""


class NoticeError(ValueError):
    pass


def connect(path):
    c = sqlite3.connect(path, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.executescript(SCHEMA)
    return c


def add_class(c, name):
    name = name.strip()
    if not name: raise NoticeError("반 이름이 비었습니다")
    c.execute("INSERT OR IGNORE INTO classes(name) VALUES(?)", (name,)); c.commit()
    return c.execute("SELECT id FROM classes WHERE name=?", (name,)).fetchone()["id"]


def class_id(c, name):
    r = c.execute("SELECT id FROM classes WHERE name=?", (name.strip(),)).fetchone()
    if not r: raise NoticeError(f"없는 반입니다: {name}")
    return r["id"]


def add_guardian(c, class_name, child, name, phone, photo_ok=False):
    digits = "".join(ch for ch in phone if ch.isdigit())
    if not (9 <= len(digits) <= 11): raise NoticeError(f"전화번호 형식이 이상합니다: {phone}")
    try:
        c.execute("INSERT INTO guardians(class_id,child,name,phone,photo_ok) VALUES(?,?,?,?,?)", (class_id(c, class_name), child.strip(), name.strip(), digits, int(photo_ok))); c.commit()
    except sqlite3.IntegrityError:
        raise NoticeError("이미 등록된 보호자입니다")


def new_token():
    return secrets.token_urlsafe(12)
