"""다채널 재고 동기화 엔진. 기준 재고(마스터)를 SQLite에 두고, 어느 채널에서 팔리든 마스터를 줄인 뒤 모든 채널에 '판매 가능 수량'을 맞춘다.
채널로 보내는 함수(pusher)는 바깥에서 넣는다. 실제 쇼핑몰 API는 연결하지 않았다."""
import csv
import json
import sqlite3


class SyncError(ValueError):
    pass


def connect(path=":memory:"):
    db = sqlite3.connect(path, check_same_thread=False, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS items(sku TEXT PRIMARY KEY, name TEXT NOT NULL, stock INTEGER NOT NULL CHECK(stock>=0))")
    db.execute("CREATE TABLE IF NOT EXISTS events(event_id TEXT PRIMARY KEY, channel TEXT, sku TEXT, qty INTEGER, result TEXT)")
    db.execute("CREATE TABLE IF NOT EXISTS pushed(sku TEXT, channel TEXT, qty INTEGER, PRIMARY KEY(sku, channel))")
    db.execute("CREATE TABLE IF NOT EXISTS log(id INTEGER PRIMARY KEY AUTOINCREMENT, msg TEXT)")
    return db


def load_config(path):
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        raise SyncError(f"설정 파일이 없습니다: {path}")
    except json.JSONDecodeError as e:
        raise SyncError(f"JSON 형식 오류: {e}")
    ch = cfg.get("channels")
    if not ch or len(set(ch)) != len(ch):
        raise SyncError("channels가 비었거나 중복입니다")
    cfg.setdefault("safety_buffer", 0)
    if not isinstance(cfg["safety_buffer"], int) or cfg["safety_buffer"] < 0:
        raise SyncError("safety_buffer는 0 이상의 정수")
    return cfg


def import_csv(db, path):
    try:
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    except FileNotFoundError:
        raise SyncError(f"파일이 없습니다: {path}")
    if not rows or not {"sku", "name", "stock"} <= set(rows[0]):
        raise SyncError("CSV에 sku,name,stock 열이 필요합니다")
    seen, clean = set(), []
    for i, r in enumerate(rows, 2):
        sku = (r["sku"] or "").strip()
        try:
            stock = int(r["stock"])
        except (TypeError, ValueError):
            raise SyncError(f"{i}행: stock이 정수가 아닙니다")
        if not sku or stock < 0 or sku in seen:
            raise SyncError(f"{i}행: sku가 비었거나 중복이거나 재고가 음수입니다")
        seen.add(sku); clean.append((sku, (r["name"] or "").strip(), stock))
    with db:
        db.executemany("INSERT OR REPLACE INTO items VALUES(?,?,?)", clean)
    return len(clean)


def sellable(stock, buffer):
    return max(stock - buffer, 0)


def sync_sku(db, cfg, sku, pusher):
    """모든 채널에 판매 가능 수량을 맞춘다. 이미 같은 값을 보낸 채널은 건너뛴다. 실패한 채널은 기록하고 나머지는 계속한다."""
    row = db.execute("SELECT stock FROM items WHERE sku=?", (sku,)).fetchone()
    if not row:
        raise SyncError(f"없는 sku: {sku}")
    qty = sellable(row[0], cfg["safety_buffer"])
    failed = []
    for ch in cfg["channels"]:
        last = db.execute("SELECT qty FROM pushed WHERE sku=? AND channel=?", (sku, ch)).fetchone()
        if last and last[0] == qty:
            continue
        try:
            pusher(ch, sku, qty)
        except Exception as e:
            failed.append(ch)
            with db:
                db.execute("INSERT INTO log(msg) VALUES(?)", (f"{sku}→{ch} 전송 실패: {e}",))
            continue
        with db:
            db.execute("INSERT OR REPLACE INTO pushed VALUES(?,?,?)", (sku, ch, qty))
    return {"sku": sku, "qty": qty, "failed": failed}


def sale(db, cfg, event_id, channel, sku, qty, pusher):
    """채널에서 판매 발생. 같은 event_id는 한 번만 처리(중복 알림 방지). 재고가 모자라면 마스터를 건드리지 않고 거부한다."""
    if channel not in cfg["channels"]:
        raise SyncError(f"모르는 채널: {channel}")
    if not isinstance(qty, int) or qty <= 0:
        raise SyncError("수량은 1 이상의 정수")
    with db:
        if db.execute("SELECT 1 FROM events WHERE event_id=?", (event_id,)).fetchone():
            return {"status": "duplicate"}
        cur = db.execute("UPDATE items SET stock=stock-? WHERE sku=? AND stock>=?", (qty, sku, qty))
        if cur.rowcount == 0:
            exists = db.execute("SELECT 1 FROM items WHERE sku=?", (sku,)).fetchone()
            if not exists:
                raise SyncError(f"없는 sku: {sku}")
            db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (event_id, channel, sku, qty, "oversold"))
            result = {"status": "oversold"}
        else:
            db.execute("INSERT INTO events VALUES(?,?,?,?,?)", (event_id, channel, sku, qty, "ok"))
            result = {"status": "ok"}
    result["sync"] = sync_sku(db, cfg, sku, pusher)
    return result


def reconcile(db, cfg, remote_stock):
    """채널에서 읽어 온 실제 수량(remote_stock[channel][sku])과 우리가 보냈어야 할 수량을 비교해 어긋난 곳을 알려 준다."""
    drift = []
    for sku, stock in db.execute("SELECT sku, stock FROM items"):
        want = sellable(stock, cfg["safety_buffer"])
        for ch in cfg["channels"]:
            got = remote_stock.get(ch, {}).get(sku)
            if got is not None and got != want:
                drift.append({"sku": sku, "channel": ch, "expected": want, "actual": got})
    return drift
