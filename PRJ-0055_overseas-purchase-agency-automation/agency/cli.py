import argparse, json
from datetime import date
from . import pricing, restrict, orders


def main(argv=None):
    p = argparse.ArgumentParser(prog="agency", description="구매대행 판매가 계산·제한 품목 확인·주문 상태 관리 (자동 수집·자동 발주 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    q = s.add_parser("quote"); q.add_argument("rules"); q.add_argument("--price-usd", type=float, required=True); q.add_argument("--ship-usd", type=float, default=0); q.add_argument("--ship-krw", type=int, default=0); q.add_argument("--category", required=True); q.add_argument("--margin", type=float)
    c = s.add_parser("check"); c.add_argument("title"); c.add_argument("--brands", default="")
    o = s.add_parser("order"); o.add_argument("file"); o.add_argument("action", choices=["new", "move", "late", "list"]); o.add_argument("--id"); o.add_argument("--item"); o.add_argument("--status"); o.add_argument("--today")
    a = p.parse_args(argv)
    try:
        if a.cmd == "quote":
            print(pricing.explain(pricing.quote({"price_usd": a.price_usd, "ship_intl_usd": a.ship_usd, "ship_domestic_krw": a.ship_krw, "category": a.category}, pricing.load_rules(a.rules), a.margin))); return 0
        if a.cmd == "check":
            fl = restrict.check(a.title, [b.strip() for b in a.brands.split(",")])
            for f in fl: print(f"[확인 필요] {f['type']} ({', '.join(f['hit'])}): {f['msg']}")
            print("걸린 항목 없음(안전하다는 뜻은 아니에요)" if not fl else f"{len(fl)}개 확인 필요"); return 0
        t = date.fromisoformat(a.today) if a.today else None
        if a.action == "new": print(orders.new(a.file, a.id, a.item or "", today=t)["status"])
        elif a.action == "move": print(orders.move(a.file, a.id, a.status, t)["status"])
        elif a.action == "late":
            for l in orders.late(a.file, t): print(f"지연: {l['id']} {l['status']} {l['days']}일 (기준 {l['limit']}일)")
        else:
            for k, v in orders.load(a.file).items(): print(k, v["status"], v["item"])
        return 0
    except (pricing.PricingError, orders.OrderError, ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
