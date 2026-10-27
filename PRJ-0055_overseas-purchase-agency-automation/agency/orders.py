"""주문 접수 상태 관리(로컬 JSON). 실제 마켓·해외 쇼핑몰에는 연결하지 않는다."""
import json, os
from datetime import date

FLOW = ["접수", "결제확인", "해외발주", "해외배송중", "통관", "국내배송중", "완료"]
LATE_DAYS = {"해외발주": 3, "해외배송중": 14, "통관": 5}


class OrderError(ValueError):
    pass


def load(path):
    if not os.path.exists(path): return {}
    try: return json.load(open(path, encoding="utf-8"))
    except ValueError: raise OrderError("주문 파일이 깨졌어요. 백업을 확인하세요")


def save(path, db):
    tmp = path + ".tmp"; json.dump(db, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, path)


def new(path, oid, item, buyer_note="", today=None):
    db = load(path)
    if oid in db: raise OrderError(f"이미 있는 주문번호예요: {oid}")
    d = (today or date.today()).isoformat(); db[oid] = {"item": item, "note": buyer_note, "status": "접수", "history": [["접수", d]]}; save(path, db); return db[oid]


def move(path, oid, status, today=None):
    db = load(path); o = db.get(oid)
    if not o: raise OrderError(f"없는 주문이에요: {oid}")
    cur = o["status"]
    if status == "취소":
        if cur in ("해외발주", "해외배송중", "통관", "국내배송중", "완료", "취소"): raise OrderError(f"'{cur}' 단계에서는 바로 취소할 수 없어요(해외 주문이 이미 진행됐어요). 직접 확인이 필요해요")
    elif status not in FLOW: raise OrderError(f"알 수 없는 상태: {status}")
    elif cur in ("취소", "완료"): raise OrderError(f"'{cur}' 주문은 상태를 바꿀 수 없어요")
    elif FLOW.index(status) != FLOW.index(cur) + 1: raise OrderError(f"'{cur}' 다음 단계는 '{FLOW[FLOW.index(cur) + 1]}'예요 (단계를 건너뛸 수 없어요)")
    o["status"] = status; o["history"].append([status, (today or date.today()).isoformat()]); save(path, db); return o


def late(path, today=None):
    today = today or date.today(); out = []
    for oid, o in load(path).items():
        lim = LATE_DAYS.get(o["status"])
        if lim:
            days = (today - date.fromisoformat(o["history"][-1][1])).days
            if days > lim: out.append({"id": oid, "status": o["status"], "days": days, "limit": lim})
    return out
