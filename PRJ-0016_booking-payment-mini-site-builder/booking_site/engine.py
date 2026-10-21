"""예약 엔진: SQLite. 같은 시간대 중복 예약은 UNIQUE 제약 + 트랜잭션으로 막는다."""
import sqlite3
from datetime import datetime
from .config import to_min

FMT = "%Y-%m-%d %H:%M"


class BookingError(ValueError):
    pass


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False, timeout=10)
    db.execute("""CREATE TABLE IF NOT EXISTS bookings(
        id INTEGER PRIMARY KEY AUTOINCREMENT, slot TEXT NOT NULL, service TEXT NOT NULL, name TEXT NOT NULL,
        price INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'confirmed', paid INTEGER NOT NULL DEFAULT 0, refunded INTEGER NOT NULL DEFAULT 0)""")
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_per_slot ON bookings(slot) WHERE status='confirmed'")
    return db


def slots_for(cfg, date):
    try: datetime.strptime(date, "%Y-%m-%d")
    except ValueError: raise BookingError("날짜는 YYYY-MM-DD 형식")
    a, b, step = to_min(cfg["open"]), to_min(cfg["close"]), cfg["slot_minutes"]
    return [f"{date} {t // 60:02d}:{t % 60:02d}" for t in range(a, b - step + 1, step)]


def free_slots(db, cfg, date):
    taken = {r[0] for r in db.execute("SELECT slot FROM bookings WHERE status='confirmed' AND slot LIKE ?", (date + "%",))}
    return [s for s in slots_for(cfg, date) if s not in taken]


def book(db, cfg, slot, service_id, name, now=None):
    name = (name or "").strip()
    if not name: raise BookingError("이름을 입력하세요")
    svc = next((s for s in cfg["services"] if s["id"] == service_id), None)
    if not svc: raise BookingError("없는 서비스입니다")
    if slot not in slots_for(cfg, slot[:10] if len(slot) >= 10 else ""):
        raise BookingError("예약할 수 없는 시간입니다")
    if (now or datetime.now()) >= datetime.strptime(slot, FMT):
        raise BookingError("지난 시간은 예약할 수 없습니다")
    try:
        with db:
            cur = db.execute("INSERT INTO bookings(slot,service,name,price) VALUES(?,?,?,?)", (slot, service_id, name, svc["price"]))
    except sqlite3.IntegrityError:
        raise BookingError("이미 예약된 시간입니다")
    return cur.lastrowid


def refund_percent(cfg, slot, now):
    hours = (datetime.strptime(slot, FMT) - now).total_seconds() / 3600
    best = 0
    for step in sorted(cfg["refund_policy"], key=lambda p: -p["hours_before"]):
        if hours >= step["hours_before"]:
            return step["percent"]
        best = step["percent"]
    return best


def cancel(db, cfg, booking_id, now=None):
    now = now or datetime.now()
    row = db.execute("SELECT slot,price,paid,status FROM bookings WHERE id=?", (booking_id,)).fetchone()
    if not row: raise BookingError("예약을 찾을 수 없습니다")
    slot, price, paid, status = row
    if status != "confirmed": raise BookingError("이미 취소된 예약입니다")
    pct = refund_percent(cfg, slot, now)
    amount = price * pct // 100 if paid else 0
    with db:
        db.execute("UPDATE bookings SET status='cancelled', refunded=? WHERE id=?", (amount, booking_id))
    return {"percent": pct, "refund": amount}
