"""예약·확인 문자(알림) 계산·답장 처리·취소 시 대기자 채우기. 문자 보내는 함수(sender)는 바깥에서 넣는다(실제 문자 발송 없음)."""
import json
import re
import sqlite3
from datetime import datetime, timedelta

FMT = "%Y-%m-%d %H:%M"
PHONE = re.compile(r"^01[016789]-?\d{3,4}-?\d{4}$")


class NoshowError(ValueError):
    pass


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS appts(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, slot TEXT,
        status TEXT NOT NULL DEFAULT 'booked')""")                   # booked / confirmed / cancelled / noshow / done / offered
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_per_slot ON appts(slot) WHERE status IN ('booked','confirmed','offered')")
    db.execute("CREATE TABLE IF NOT EXISTS sent(appt_id INTEGER, hours INTEGER, PRIMARY KEY(appt_id, hours))")
    db.execute("CREATE TABLE IF NOT EXISTS waitlist(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, slot TEXT, status TEXT NOT NULL DEFAULT 'waiting', offer_expires TEXT)")
    return db


def load_config(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise NoshowError(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise NoshowError(f"JSON 형식 오류: {e}")
    if not cfg.get("shop") or not cfg.get("template"):
        raise NoshowError("shop과 template이 필요합니다")
    hs = cfg.setdefault("remind_hours_before", [24, 2])
    if not hs or any(not isinstance(h, int) or h <= 0 for h in hs):
        raise NoshowError("remind_hours_before는 1 이상의 정수 목록")
    cfg.setdefault("offer_valid_minutes", 15)
    return cfg


def _check(name, phone, slot):
    if not (name or "").strip(): raise NoshowError("이름이 비었습니다")
    if not PHONE.match(phone or ""): raise NoshowError("휴대폰 번호 형식이 올바르지 않습니다")
    try: datetime.strptime(slot, FMT)
    except ValueError: raise NoshowError("시간은 YYYY-MM-DD HH:MM 형식")


def add(db, name, phone, slot):
    _check(name, phone, slot)
    try:
        with db:
            return db.execute("INSERT INTO appts(name,phone,slot) VALUES(?,?,?)", (name.strip(), phone, slot)).lastrowid
    except sqlite3.IntegrityError:
        raise NoshowError("이미 예약된 시간입니다")


def due_reminders(db, cfg, now):
    """지금 보내야 할 알림 목록. 같은 예약·같은 시점은 한 번만."""
    out = []
    for aid, name, phone, slot, status in db.execute("SELECT id,name,phone,slot,status FROM appts WHERE status IN ('booked','confirmed')"):
        t = datetime.strptime(slot, FMT)
        if t <= now: continue
        for h in sorted(cfg["remind_hours_before"], reverse=True):
            if t - timedelta(hours=h) <= now and not db.execute("SELECT 1 FROM sent WHERE appt_id=? AND hours=?", (aid, h)).fetchone():
                if status == "confirmed" and h != min(cfg["remind_hours_before"]): continue      # 이미 확인한 손님에겐 마지막 알림만
                out.append({"appt_id": aid, "hours": h, "phone": phone,
                            "text": cfg["template"].format(shop=cfg["shop"], name=name, when=t.strftime("%m월 %d일 %H:%M"))})
                break                                                                           # 한 번에 하나(가장 이른 미발송 시점만)
    return out


def send_due(db, cfg, now, sender):
    sent = 0
    for r in due_reminders(db, cfg, now):
        try:
            sender(r["phone"], r["text"])
        except Exception:
            continue                                                                           # 실패하면 기록하지 않아 다음에 다시 시도
        with db:
            db.execute("INSERT OR IGNORE INTO sent VALUES(?,?)", (r["appt_id"], r["hours"]))
        sent += 1
    return sent


def handle_reply(db, cfg, phone, text, now, sender):
    """손님 답장 처리: 1=확인, 2=취소. 대기자 제안에는 '네/예'(수락) '아니오'(거절). 알아듣지 못하면 None."""
    t = (text or "").strip().replace(" ", "")
    offered = db.execute("SELECT id,slot FROM appts WHERE phone=? AND status='offered' ORDER BY id DESC LIMIT 1", (phone,)).fetchone()
    if offered:
        if t in ("1", "네", "예", "수락", "yes", "Y", "y"):
            with db: db.execute("UPDATE appts SET status='confirmed' WHERE id=?", (offered[0],))
            return "offer_accepted"
        if t in ("2", "아니오", "아니요", "거절", "no", "N", "n"):
            with db: db.execute("UPDATE appts SET status='cancelled' WHERE id=?", (offered[0],))
            _offer_next(db, cfg, offered[1], now, sender)
            return "offer_declined"
    row = db.execute("SELECT id,slot FROM appts WHERE phone=? AND status IN ('booked','confirmed') AND slot>? ORDER BY slot LIMIT 1", (phone, now.strftime(FMT))).fetchone()
    if not row: return None
    if t == "1":
        with db: db.execute("UPDATE appts SET status='confirmed' WHERE id=?", (row[0],))
        return "confirmed"
    if t in ("2", "취소"):
        with db: db.execute("UPDATE appts SET status='cancelled' WHERE id=?", (row[0],))
        _offer_next(db, cfg, row[1], now, sender)
        return "cancelled"
    return None


def join_waitlist(db, name, phone, slot):
    _check(name, phone, slot)
    with db:
        return db.execute("INSERT INTO waitlist(name,phone,slot) VALUES(?,?,?)", (name.strip(), phone, slot)).lastrowid


def _offer_next(db, cfg, slot, now, sender):
    """빈 시간을 대기자 중 가장 먼저 등록한 사람에게 제안(제한 시간 안에 답이 없으면 expire_offers가 다음 사람에게 넘김)."""
    w = db.execute("SELECT id,name,phone FROM waitlist WHERE slot=? AND status='waiting' ORDER BY id LIMIT 1", (slot,)).fetchone()
    if not w: return None
    exp = (now + timedelta(minutes=cfg["offer_valid_minutes"])).strftime(FMT)
    with db:
        db.execute("UPDATE waitlist SET status='offered', offer_expires=? WHERE id=?", (exp, w[0]))
        db.execute("INSERT INTO appts(name,phone,slot,status) VALUES(?,?,?,'offered')", (w[1], w[2], slot))
    try:
        sender(w[2], f"[{cfg['shop']}] {w[1]}님, {slot[5:10]} {slot[11:]} 자리가 비었습니다. {cfg['offer_valid_minutes']}분 안에 1(예약)/2(거절)을 보내주세요.")
    except Exception:
        pass
    return w[0]


def expire_offers(db, cfg, now, sender):
    n = 0
    for aid, slot, phone in db.execute("SELECT a.id,a.slot,a.phone FROM appts a JOIN waitlist w ON w.phone=a.phone AND w.slot=a.slot AND w.status='offered' WHERE a.status='offered' AND w.offer_expires<=?", (now.strftime(FMT),)).fetchall():
        with db:
            db.execute("UPDATE appts SET status='cancelled' WHERE id=?", (aid,))
            db.execute("UPDATE waitlist SET status='expired' WHERE phone=? AND slot=? AND status='offered'", (phone, slot))
        _offer_next(db, cfg, slot, now, sender); n += 1
    return n


def mark_done(db, appt_id):
    """직원이 '방문 완료'를 표시한다. 표시하지 않은 지난 예약은 mark_noshows가 노쇼로 처리한다."""
    with db:
        cur = db.execute("UPDATE appts SET status='done' WHERE id=? AND status IN ('booked','confirmed')", (appt_id,))
    if cur.rowcount == 0:
        raise NoshowError("방문 완료로 바꿀 수 있는 예약이 아닙니다")


def mark_noshows(db, now):
    with db:
        cur = db.execute("UPDATE appts SET status='noshow' WHERE status IN ('booked','confirmed') AND slot<=?", (now.strftime(FMT),))
    return cur.rowcount


def noshow_rate(db, phone):
    done, ns = db.execute("SELECT SUM(status='done'), SUM(status='noshow') FROM appts WHERE phone=?", (phone,)).fetchone()
    total = (done or 0) + (ns or 0)
    return None if not total else round(100 * (ns or 0) / total, 1)
