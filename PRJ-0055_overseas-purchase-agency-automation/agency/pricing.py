"""구매대행 판매가·마진 계산. **관세·부가세 규칙과 수수료율은 사용자가 rules.json에 넣는 값(샘플은 예시)이며 실제 세법·마켓 수수료가 아니다.**"""
import json


class PricingError(ValueError):
    pass


def load_rules(path):
    try: r = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise PricingError(f"규칙 파일을 읽지 못했습니다: {e}")
    for k in ("usd_krw", "rate_date", "duty_free_usd", "vat", "market_fee", "min_margin_pct", "categories"):
        if k not in r: raise PricingError(f"규칙 파일에 '{k}'가 없습니다")
    return r


def quote(item, rules, target_margin_pct=None):
    """item: price_usd, ship_intl_usd, ship_domestic_krw, category. 반환: 원가 분해, 판매가, 이익."""
    for k in ("price_usd", "ship_intl_usd", "category"):
        if item.get(k) is None: raise PricingError(f"상품 정보에 '{k}'가 없습니다")
    if item["price_usd"] <= 0: raise PricingError("상품 가격은 0보다 커야 합니다")
    cat = rules["categories"].get(item["category"])
    if cat is None: raise PricingError(f"알 수 없는 분류 '{item['category']}' (규칙 파일의 categories에 없음)")
    fx = rules["usd_krw"]; goods = item["price_usd"] * fx; ship = item["ship_intl_usd"] * fx
    cif_usd = item["price_usd"] + item["ship_intl_usd"]
    taxable = cif_usd > rules["duty_free_usd"]
    duty = round((goods + ship) * cat["duty"]) if taxable else 0
    vat = round((goods + ship + duty) * rules["vat"]) if taxable else 0
    dom = item.get("ship_domestic_krw", 0)
    cost = round(goods + ship) + duty + vat + dom
    m = (target_margin_pct if target_margin_pct is not None else rules["min_margin_pct"]) / 100
    fee = rules["market_fee"]
    price = cost / (1 - fee - m)                      # 판매가 × (1 - 수수료 - 마진) = 원가
    price = int(-(-price // 100) * 100)               # 100원 단위 올림
    profit = round(price * (1 - fee) - cost)
    return {"goods": round(goods), "ship_intl": round(ship), "duty": duty, "vat": vat, "ship_dom": dom, "cost": cost, "price": price, "fee": round(price * fee), "profit": profit, "margin_pct": round(profit / price * 100, 1), "taxable": taxable, "rate_date": rules["rate_date"]}


def explain(q):
    t = [f"상품 {q['goods']:,}원 + 해외배송 {q['ship_intl']:,}원 + 관세 {q['duty']:,}원 + 부가세 {q['vat']:,}원 + 국내배송 {q['ship_dom']:,}원 = 원가 {q['cost']:,}원",
         f"판매가 {q['price']:,}원 → 마켓 수수료 {q['fee']:,}원 → 이익 {q['profit']:,}원 (마진 {q['margin_pct']}%)", f"(환율 입력값 기준일 {q['rate_date']}. 면세 한도 이하: {'아니오' if q['taxable'] else '예'})"]
    return "\n".join(t)
