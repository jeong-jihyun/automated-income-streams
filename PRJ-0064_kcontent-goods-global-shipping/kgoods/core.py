"""K-콘텐츠 굿즈 해외 직배송 견적·제한 점검 (요금표·세금 기준은 입력값, 실제 발송 없음)."""
import csv, math

CATS = {"앨범", "포토카드", "의류", "문구", "액세서리", "응원봉", "화장품", "식품"}
VOL_DIV = 5000     # 부피무게 = 가로*세로*높이(cm) / 5000 (일반적인 예시 값)


def vol_weight(l, w, h):
    return l * w * h / VOL_DIV * 1000      # g


def bill_weight(actual_g, l, w, h, step=100):
    v = vol_weight(l, w, h) if all((l, w, h)) else 0
    b = max(actual_g, v)
    return int(math.ceil(b / step) * step), round(v)


def rate(table, country, grams):
    z = table["countries"].get(country)
    if not z: raise ValueError(f"요금표에 없는 국가: {country}")
    zone = table["zones"][z]
    if grams > zone["max_g"]: raise ValueError(f"{country}: {grams}g는 최대 {zone['max_g']}g 초과")
    steps = math.ceil(max(grams - zone["base_g"], 0) / zone["step_g"])
    return zone["base_fee"] + steps * zone["step_fee"]


def check_items(items, country, rules):
    block, warn = [], []
    r = rules.get(country, {})
    for it in items:
        cat = it["category"]
        if cat not in CATS: block.append(f"{it['name']}: 알 수 없는 분류 '{cat}'")
        if not it.get("licensed"):
            block.append(f"{it['name']}: 공식 라이선스 상품 표시가 없어 발송 불가(비공식 굿즈 판매 금지)")
        if cat in r.get("banned_categories", []): block.append(f"{it['name']}: {country}은(는) '{cat}' 반입 제한(예시 규칙)")
        if it.get("battery") and r.get("no_battery", True): block.append(f"{it['name']}: 배터리 포함 상품은 항공 발송 제한(예시 규칙)")
        if cat in ("화장품", "식품"): warn.append(f"{it['name']}: 화장품·식품은 수입 신고/표기 규정을 따로 확인")
    return block, warn


def duty_note(country, value_usd, rules):
    t = rules.get(country, {}).get("duty_free_usd")
    if t is None: return f"{country}: 면세 한도 정보 없음 - 직접 확인 필요"
    if value_usd <= t: return f"신고가 ${value_usd:.0f} <= 면세 한도 ${t} (예시값, 소비자 부담 세금 없을 수 있음)"
    return f"신고가 ${value_usd:.0f} > 면세 한도 ${t} (예시값): 관세/부가세가 붙을 수 있음, 고객에게 사전 안내 필요"


def quote(order, table, rules, krw_per_usd):
    items = order["items"]; c = order["country"]
    block, warn = check_items(items, c, rules)
    actual = sum(i["weight_g"] * i.get("qty", 1) for i in items)
    box = order.get("box") or {}
    billed, vol = bill_weight(actual + order.get("packing_g", 0), box.get("l", 0), box.get("w", 0), box.get("h", 0))
    goods = sum(i["price_krw"] * i.get("qty", 1) for i in items)
    out = {"id": order["id"], "country": c, "actual_g": actual, "volume_g": vol, "billed_g": billed,
           "goods_krw": goods, "block": block, "warn": warn}
    if block:
        out["status"] = "발송불가"; return out
    try:
        ship = rate(table, c, billed)
    except ValueError as e:
        out["status"] = "발송불가"; out["block"] = [str(e) + " (나눠 포장하거나 다른 방법 필요)"]; return out
    out.update(status="견적가능", ship_krw=ship, total_krw=goods + ship, declared_usd=round(goods / krw_per_usd, 2),
               duty=duty_note(c, goods / krw_per_usd, rules))
    return out


def read_orders(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    need = {"id", "country", "name", "category", "qty", "weight_g", "price_krw", "licensed"}
    if rows and need - set(rows[0]): raise ValueError("필수 열이 없습니다: " + ", ".join(sorted(need - set(rows[0]))))
    orders = {}
    for r in rows:
        try:
            it = {"name": r["name"], "category": r["category"], "qty": int(r["qty"]), "weight_g": int(r["weight_g"]),
                  "price_krw": int(r["price_krw"]), "licensed": r["licensed"].strip().lower() in ("y", "yes", "true", "1", "예"),
                  "battery": r.get("battery", "").strip().lower() in ("y", "yes", "true", "1", "예")}
        except ValueError:
            raise ValueError(f"주문 {r.get('id')}: 숫자 칸 형식 오류")
        if it["qty"] < 1 or it["weight_g"] <= 0 or it["price_krw"] < 0: raise ValueError(f"주문 {r['id']}: 수량·무게·가격 값 오류")
        o = orders.setdefault(r["id"], {"id": r["id"], "country": r["country"], "items": []})
        if o["country"] != r["country"]: raise ValueError(f"주문 {r['id']}: 국가가 행마다 다릅니다")
        o["items"].append(it)
        for k, d in (("l", "box_l"), ("w", "box_w"), ("h", "box_h")):
            if r.get(d): o.setdefault("box", {})[k] = float(r[d])
    return list(orders.values())


def report(qs):
    L = []
    for q in qs:
        if q["status"] == "발송불가":
            L.append(f"[{q['id']}] 발송불가 ({q['country']}): " + " / ".join(q["block"]))
        else:
            L.append(f"[{q['id']}] {q['country']} 청구무게 {q['billed_g']}g(실무게 {q['actual_g']}g, 부피 {q['volume_g']}g) 배송비 {q['ship_krw']:,}원, 상품 {q['goods_krw']:,}원, 합계 {q['total_krw']:,}원")
            L.append("    " + q["duty"])
            for w in q["warn"]: L.append("    주의: " + w)
    L.append("※ 요금표·면세 한도·반입 제한은 예시 입력값입니다. 실제 운송사 요금과 각국 규정을 확인하세요. 발송·결제는 하지 않습니다.")
    return "\n".join(L)
