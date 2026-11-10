"""도매 상품 정보 정리 + 판매가 계산 + 등록용 CSV 내보내기 (수집·자동 등록 없음)."""
import csv, io, math, re

NEED = ["supplier", "name", "cost", "moq", "stock", "ship_fee", "image"]
KO = {"도매처": "supplier", "상품명": "name", "도매가": "cost", "최소주문": "moq", "재고": "stock",
      "배송비": "ship_fee", "이미지": "image", "원산지": "origin"}
DEFAULT = {"fee_rate": 0.06, "margin_rate": 0.15, "round_to": 10, "min_stock": 5,
           "ship_share": 1.0, "banned": ["최저가", "1위", "무조건", "100%"], "brand_watch": ["나이키", "아디다스", "샤넬", "정품"]}


def _num(v):
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def clean_name(s, supplier=""):
    s = re.sub(r"\[[^\]]*\]|\([^)]*도매[^)]*\)", " ", s or "")
    s = re.sub(r"[★☆♥♡◆■●▶※]+", " ", s)
    if supplier:
        s = s.replace(supplier, " ")
    return re.sub(r"\s+", " ", s).strip()


def price(cost, ship, cfg):
    """판매가 = (원가 + 배송비 분담) / (1 - 수수료율 - 마진율), 올림."""
    d = 1 - cfg["fee_rate"] - cfg["margin_rate"]
    if d <= 0:
        raise ValueError("수수료율+마진율이 100% 이상입니다")
    raw = (cost + ship * cfg["ship_share"]) / d
    u = cfg["round_to"]
    return int(math.ceil(raw / u) * u)


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        head = [KO.get(h.strip(), h.strip()) for h in (rd.fieldnames or [])]
        rows = [{head[i]: (v or "").strip() for i, v in enumerate(r.values()) if i < len(head)} for r in rd]
    miss = [c for c in NEED if c not in head]
    if miss:
        raise ValueError("필수 열이 없습니다: " + ", ".join(miss))
    return rows, [h for h in head if h not in NEED and h != "origin"]


def run(path, cfg=None):
    c = dict(DEFAULT); c.update(cfg or {})
    rows, ignored = read(path)
    ok, hold, seen = [], [], {}
    for i, r in enumerate(rows, start=2):
        why, warn = [], []
        name = clean_name(r["name"], r["supplier"])
        cost, ship, moq, stock = _num(r["cost"]), _num(r["ship_fee"]), _num(r["moq"]), _num(r["stock"])
        if not name: why.append("상품명이 비어 있음")
        if cost is None or cost <= 0: why.append("도매가가 숫자가 아님")
        if ship is None or ship < 0: why.append("배송비가 숫자가 아님")
        if stock is None: why.append("재고가 숫자가 아님")
        elif stock < c["min_stock"]: why.append(f"재고 {int(stock)}개 (기준 {c['min_stock']}개 미만)")
        if moq is None or moq < 1: why.append("최소주문수량이 숫자가 아님")
        if not r["image"]: why.append("이미지 주소 없음")
        elif not r["image"].lower().startswith("https://"): warn.append("이미지가 https 주소가 아님")
        for b in c["banned"]:
            if b in name: why.append(f"금지어 '{b}'")
        for b in c["brand_watch"]:
            if b in name: warn.append(f"상표/정품 표현 '{b}' - 권리 확인 필요")
        key = name.replace(" ", "")
        if key and key in seen: why.append(f"{seen[key]}행과 상품명 중복")
        elif key: seen[key] = i
        if why:
            hold.append({"row": i, "name": name or r["name"], "why": "; ".join(why)}); continue
        sp = price(cost, ship, c)
        profit = sp - sp * c["fee_rate"] - cost - ship * c["ship_share"]
        if moq > 1: warn.append(f"최소주문 {int(moq)}개 - 소량 판매 시 재고 부담")
        ok.append({"row": i, "supplier": r["supplier"], "name": name, "cost": int(cost), "ship_fee": int(ship),
                   "price": sp, "profit": round(profit), "margin_pct": round(profit / sp * 100, 1),
                   "stock": int(stock), "moq": int(moq), "image": r["image"], "origin": r.get("origin", ""),
                   "warn": "; ".join(warn)})
    return {"ok": ok, "hold": hold, "ignored": ignored, "total": len(rows), "cfg": c}


def _safe(v):
    v = "" if v is None else str(v)
    return "'" + v if v and v[0] in "=+-@" else v


COLS = ["row", "supplier", "name", "cost", "ship_fee", "price", "profit", "margin_pct", "stock", "moq", "origin", "image", "warn"]
LAB = ["원본행", "도매처", "상품명", "도매가", "배송비", "판매가", "예상이익", "이익률(%)", "재고", "최소주문", "원산지", "이미지", "주의"]


def export_ok(res, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(LAB)
        for r in res["ok"]:
            w.writerow([_safe(r[c]) for c in COLS])
        w.writerow([])
        w.writerow(["※ 이 파일은 정리 결과일 뿐 자동 등록하지 않습니다. 도매처 재고·가격은 등록 직전에 다시 확인하세요."])


def export_hold(res, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["원본행", "상품명", "보류 이유"])
        for r in res["hold"]:
            w.writerow([r["row"], _safe(r["name"]), r["why"]])


def summary(res):
    o, h = res["ok"], res["hold"]
    L = [f"전체 {res['total']}개 중 등록 후보 {len(o)}개, 보류 {len(h)}개"]
    if res["ignored"]: L.append("무시한 열: " + ", ".join(res["ignored"]))
    for r in o:
        L.append(f"  - {r['name']}: 판매가 {r['price']:,}원 (이익 {r['profit']:,}원, {r['margin_pct']}%)" + (f" ⚠ {r['warn']}" if r["warn"] else ""))
    for r in h:
        L.append(f"  - [보류] {r['row']}행 {r['name']}: {r['why']}")
    L.append("※ 수수료율·마진율은 예시 설정값입니다. 실제 마켓 수수료와 도매처 최신 재고를 확인하세요.")
    return "\n".join(L)
