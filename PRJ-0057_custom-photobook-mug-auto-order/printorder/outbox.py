"""제작사 전달함: 주문을 한 번만 보내고, 실패하면 재시도 횟수를 세며, 3번 실패하면 사람이 확인하게 한다. 제작사 전송 함수는 바깥에서 꽂는다(실제 제작사에는 연결하지 않았다)."""
import json, os

MAX_ATTEMPTS = 3


class OutboxError(ValueError):
    pass


def load(path):
    if not os.path.exists(path): return {}
    try: return json.load(open(path, encoding="utf-8"))
    except ValueError: raise OutboxError("전달함 파일이 깨졌어요")


def save(path, db):
    tmp = path + ".tmp"; json.dump(db, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, path)


def validate_order(o):
    for k in ("order_id", "product", "files", "quantity"):
        if not o.get(k): raise OutboxError(f"주문에 '{k}'가 없어요")
    if not isinstance(o["quantity"], int) or not 1 <= o["quantity"] <= 100: raise OutboxError("수량은 1~100 정수여야 해요")
    missing = [f for f in o["files"] if not os.path.exists(f)]
    if missing: raise OutboxError(f"인쇄 파일이 없어요: {missing}")


def dispatch(path, order, sender):
    """반환: sent / already_sent / failed / needs_manual"""
    validate_order(order); db = load(path); rec = db.setdefault(order["order_id"], {"status": "pending", "attempts": 0, "error": ""})
    if rec["status"] == "sent": return "already_sent"
    if rec["status"] == "needs_manual": return "needs_manual"
    rec["attempts"] += 1
    try:
        sender(order); rec["status"], rec["error"] = "sent", ""; result = "sent"
    except Exception as e:                                   # 전송 실패(제작사 오류 등)는 기록하고 재시도 대상으로 남긴다
        rec["error"] = f"{type(e).__name__}: {e}"; rec["status"] = "needs_manual" if rec["attempts"] >= MAX_ATTEMPTS else "pending"; result = "needs_manual" if rec["status"] == "needs_manual" else "failed"
    save(path, db); return result
