import argparse
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="inventory_sync", description="다채널 재고 동기화 엔진 (실제 쇼핑몰 연결 없음, 시험용 출력)")
    p.add_argument("--db", default="inventory.db"); p.add_argument("--config", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("import").add_argument("--csv", required=True)
    s = sub.add_parser("sale"); s.add_argument("event_id"); s.add_argument("channel"); s.add_argument("sku"); s.add_argument("qty", type=int)
    sub.add_parser("show")
    a = p.parse_args(argv)
    try:
        cfg = core.load_config(a.config); db = core.connect(a.db)
        pusher = lambda ch, sku, qty: print(f"  → [{ch}] {sku} 판매가능 {qty}개 (시험 출력, 실제 전송 아님)")
        if a.cmd == "import":
            print(f"{core.import_csv(db, a.csv)}개 상품을 불러왔습니다")
        elif a.cmd == "sale":
            r = core.sale(db, cfg, a.event_id, a.channel, a.sku, a.qty, pusher); print("결과:", r["status"])
        else:
            for sku, name, stock in db.execute("SELECT sku,name,stock FROM items ORDER BY sku"):
                print(f"{sku} {name}: 기준 재고 {stock} / 판매가능 {core.sellable(stock, cfg['safety_buffer'])}")
        return 0
    except core.SyncError as e:
        print(f"[오류] {e}"); return 2
