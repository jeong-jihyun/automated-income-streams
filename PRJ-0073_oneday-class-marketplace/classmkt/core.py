"""원데이 클래스 예약(정원·대기)·취소 환불·강사 정산 계산. 결제·정산 송금은 하지 않는다."""
import csv, datetime as dt, json
from collections import defaultdict

REFUND_POLICY = [(7, 1.0), (3, 0.5), (1, 0.3)]      # (수업 며칠 전까지, 환불 비율) - 예시. 그 밖은 0%


def load_classes(path):
    out = {}
    for c in json.load(open(path, encoding="utf-8")):
        for k in ("id", "title", "instructor", "price", "capacity", "start"):
            if k not in c: raise ValueError(f"클래스에 '{k}'가 없습니다: {c}")
        if c["id"] in out: raise ValueError(f"클래스 id 중복: {c['id']}")
        if not isinstance(c["capacity"], int) or c["capacity"] < 1 or c["price"] < 0: raise ValueError(f"{c['id']}: 정원·가격 값 오류")
        c["start"] = dt.datetime.fromisoformat(c["start"]); c.setdefault("min_students", 1)
        out[c["id"]] = c
    return out


def refund_ratio(days_before, policy=None):
    for d, ratio in (policy or REFUND_POLICY):
        if days_before >= d: return ratio
    return 0.0


def process(classes, bookings_path, policy=None):
    state = {cid: {"confirmed": [], "wait": [], "paid": 0, "refunded": 0} for cid in classes}; log, errors = [], []
    with open(bookings_path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    try: rows.sort(key=lambda r: dt.datetime.fromisoformat(r["time"]))
    except (ValueError, KeyError): raise ValueError("bookings 파일의 time 열(ISO 형식)을 확인하세요")
    for i, r in enumerate(rows, start=2):
        cid, who, act, t = r["class_id"].strip(), r["student"].strip(), r["action"].strip().lower(), dt.datetime.fromisoformat(r["time"])
        if cid not in classes: errors.append((i, who, "없는 클래스")); continue
        c, s = classes[cid], state[cid]
        if act == "book":
            if t >= c["start"]: errors.append((i, who, "이미 시작한 수업")); continue
            if who in s["confirmed"] or who in s["wait"]: errors.append((i, who, "이미 신청함")); continue
            if len(s["confirmed"]) < c["capacity"]: s["confirmed"].append(who); s["paid"] += c["price"]; log.append((t, cid, who, "확정"))
            else: s["wait"].append(who); log.append((t, cid, who, "대기"))
        elif act == "cancel":
            if who in s["wait"]: s["wait"].remove(who); log.append((t, cid, who, "대기 취소")); continue
            if who not in s["confirmed"]: errors.append((i, who, "취소할 신청이 없음")); continue
            days = (c["start"] - t).total_seconds() / 86400
            ref = int(c["price"] * refund_ratio(days, policy)); s["confirmed"].remove(who); s["refunded"] += ref; log.append((t, cid, who, f"취소(환불 {ref:,}원)"))
            if s["wait"] and t < c["start"]:
                nxt = s["wait"].pop(0); s["confirmed"].append(nxt); s["paid"] += c["price"]; log.append((t, cid, nxt, "대기→확정"))
        else: errors.append((i, who, f"알 수 없는 action '{act}'"))
    return state, log, errors


def settle(classes, state, commission=0.15, cancel_check=None):
    """cancel_check: 이 시각 기준으로 최소 인원 미달 클래스를 폐강 후보로 표시하고 전액 환불로 계산."""
    inst = defaultdict(lambda: {"net": 0, "fee": 0, "pay": 0}); rows = []
    for cid, c in classes.items():
        s = state[cid]; n = len(s["confirmed"]); closed = bool(cancel_check and cancel_check < c["start"] and n < c["min_students"] and n > 0)
        paid, refunded = s["paid"], s["refunded"]
        if closed: refunded = paid          # 전원 전액 환불
        net = paid - refunded; fee = int(net * commission); pay = net - fee
        rows.append({"id": cid, "title": c["title"], "instructor": c["instructor"], "confirmed": n, "capacity": c["capacity"], "waiting": len(s["wait"]), "paid": paid, "refunded": refunded, "fee": fee, "pay": pay, "closed": closed})
        a = inst[c["instructor"]]; a["net"] += net; a["fee"] += fee; a["pay"] += pay
    return rows, dict(inst)


def text(rows, inst, log, errors):
    L = []
    for r in rows:
        L.append(f"[{r['id']}] {r['title']} - 확정 {r['confirmed']}/{r['capacity']}, 대기 {r['waiting']}, 결제 {r['paid']:,} 환불 {r['refunded']:,} 수수료 {r['fee']:,} 강사 정산 {r['pay']:,}" + (" ⚠ 최소 인원 미달 폐강 후보(전액 환불로 계산)" if r["closed"] else ""))
    L += [f"강사 {k}: 정산 예정 {v['pay']:,}원 (수수료 {v['fee']:,}원)" for k, v in sorted(inst.items())]
    L += [f"처리 안 됨: {i}행 {w} - {m}" for i, w, m in errors]
    L.append("※ 환불 비율·수수료율은 예시입니다. 결제·송금은 하지 않으며 강사 자격·안전·보험은 확인하지 않았습니다.")
    return "\n".join(L)
