"""캠핑·차박 세트 구성기: 인원·계절·방식·예산에 맞춰 필수 카테고리를 채우고, 재고·수용 인원·보온 등급·마진을 확인한다. 카탈로그는 사용자가 넣은 자료다."""
import json, math

MIN_TEMP = {"봄가을": 5, "여름": 15, "겨울": -5}   # 계절 최저기온 예시값(°C)
REQUIRED = {"캠핑": ["텐트", "침낭", "매트", "의자", "조명", "취사"], "차박": ["매트", "침낭", "조명", "취사", "햇빛가리개"]}
PER_PERSON = {"침낭", "매트", "의자"}              # 사람 수만큼 필요한 카테고리
BUNDLE_MIN_ITEMS, BUNDLE_DISCOUNT = 4, 0.05


class SetError(ValueError):
    pass


def load(path):
    try: d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise SetError(f"카탈로그를 읽지 못했습니다: {e}")
    for i, p in enumerate(d):
        for k in ("id", "name", "category", "cost", "price", "stock"):
            if p.get(k) is None: raise SetError(f"{i + 1}번째 상품에 '{k}'가 없습니다")
        if p["price"] < p["cost"]: raise SetError(f"{p['id']}: 판매가가 원가보다 낮아요")
    return d


def qty_needed(item, persons):
    if item["category"] in PER_PERSON: return math.ceil(persons / item.get("capacity", 1))
    return 1


def candidates(cat, catalog, persons, season):
    out = []
    for p in catalog:
        if p["category"] != cat: continue
        if p.get("seasons") and season not in p["seasons"]: continue
        if cat == "텐트" and p.get("capacity", 1) < persons: continue
        if cat == "침낭" and p.get("comfort_c", 99) > MIN_TEMP[season]: continue
        if p["stock"] < qty_needed(p, persons): continue
        out.append(p)
    return sorted(out, key=lambda p: (p["price"] * qty_needed(p, persons), p["id"]))


def totals(picks, persons):
    price = sum(p["price"] * qty_needed(p, persons) for p in picks); cost = sum(p["cost"] * qty_needed(p, persons) for p in picks)
    if len(picks) >= BUNDLE_MIN_ITEMS: price = int(round(price * (1 - BUNDLE_DISCOUNT), -2))
    return price, cost


def build(catalog, persons, season, mode, budget, min_margin_pct=10):
    if persons < 1: raise SetError("인원은 1명 이상이어야 해요")
    if season not in MIN_TEMP: raise SetError(f"계절은 {list(MIN_TEMP)} 중 하나")
    if mode not in REQUIRED: raise SetError(f"방식은 {list(REQUIRED)} 중 하나")
    cats = REQUIRED[mode]; opts = {c: candidates(c, catalog, persons, season) for c in cats}
    missing = [c for c in cats if not opts[c]]
    if missing: return {"ok": False, "reason": f"조건에 맞는 상품이 없는 분류: {missing} (재고·인원·계절·보온 등급 확인)", "missing": missing}
    idx = {c: 0 for c in cats}; pick = lambda: [opts[c][idx[c]] for c in cats]
    price, cost = totals(pick(), persons)
    if price > budget: return {"ok": False, "reason": f"가장 저렴한 구성도 {price:,}원이라 예산 {budget:,}원을 넘어요", "min_price": price, "missing": []}
    upgraded = True
    while upgraded:                                     # 예산 안에서 앞 분류부터 한 단계씩 상위 상품으로 교체
        upgraded = False
        for c in cats:
            if idx[c] + 1 < len(opts[c]):
                idx[c] += 1; np_, nc = totals(pick(), persons)
                if np_ <= budget: price, cost, upgraded = np_, nc, True
                else: idx[c] -= 1
    items = [{"id": p["id"], "name": p["name"], "category": p["category"], "qty": qty_needed(p, persons)} for p in pick()]
    margin = round((price - cost) / price * 100, 1); warn = []
    if margin < min_margin_pct: warn.append(f"마진 {margin}%가 최소 {min_margin_pct}%보다 낮아요")
    for p in pick():
        if p["stock"] - qty_needed(p, persons) < 3: warn.append(f"재고 부족 임박: {p['name']} (재고 {p["stock"]}개)")
    return {"ok": True, "items": items, "price": price, "cost": cost, "margin_pct": margin, "bundle": len(items) >= BUNDLE_MIN_ITEMS, "warnings": warn}


def render(r, persons, season, mode, budget):
    if not r["ok"]: return f"세트를 만들 수 없어요: {r['reason']}"
    L = [f"# {mode} 세트 — {persons}명 · {season} · 예산 {budget:,}원", ""] + [f"- [{i['category']}] {i['name']} × {i['qty']}" for i in r["items"]]
    L += ["", f"세트 가격: {r['price']:,}원" + (f" (구성 {BUNDLE_MIN_ITEMS}개 이상 {int(BUNDLE_DISCOUNT * 100)}% 묶음 할인 반영)" if r["bundle"] else ""), f"(내부) 원가 {r['cost']:,}원 · 마진 {r['margin_pct']}%"]
    L += [f"⚠ {w}" for w in r["warnings"]]
    return "\n".join(L)
