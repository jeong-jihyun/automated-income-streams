import argparse
import json
import time
from . import adapters, server
from .gateway import Gateway


def demo_fetchers():
    """서버 시험용 가짜 채널 응답(실제 API 아님)."""
    return {
        "naver": lambda: {"data": {"orders": [{"orderId": "N1", "orderStatus": "PAYED", "totalPaymentAmount": 12000, "buyerName": "가", "orderDate": "2030-01-02"}]}},
        "coupang": lambda: {"orders": [{"orderId": 77, "status": "ACCEPT", "orderPrice": 8000, "receiver": {"name": "나"}, "orderedAt": "2030-01-03"}]},
        "kakao": lambda: {"result": [{"order_id": "K9", "state": "done", "amount": {"total": 5000}, "buyer": {"nickname": "다"}, "created_at": "2030-01-01"}]},
    }


def main(argv=None):
    p = argparse.ArgumentParser(prog="kr_gateway", description="국내 커머스 주문 통합 게이트웨이 (시험용·가짜 채널 응답)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("check", "serve"):
        s = sub.add_parser(n); s.add_argument("--mappings", required=True); s.add_argument("--keys", required=True)
        if n == "serve": s.add_argument("--port", type=int, default=8090)
    a = p.parse_args(argv)
    try:
        maps = adapters.load_mappings(a.mappings)
        keys = json.load(open(a.keys, encoding="utf-8"))["keys"]
    except (adapters.AdapterError, FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
    print(f"설정 확인: 채널 {', '.join(maps)} / 키 {len(keys)}개")
    if a.cmd == "serve":
        print(f"시험용 서버 http://127.0.0.1:{a.port}/v1/orders (헤더 X-API-Key 필요). 실제 쇼핑몰 API에는 연결되지 않습니다.")
        server.serve(Gateway(keys, maps, demo_fetchers(), time.time), a.port)
    return 0
