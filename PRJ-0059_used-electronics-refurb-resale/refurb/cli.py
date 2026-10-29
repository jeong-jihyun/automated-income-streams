import argparse, json
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="refurb", description="중고 전자기기 매입가·등급·판매 글 (시세는 CSV로 입력, 수집 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    q = s.add_parser("quote"); q.add_argument("comps"); q.add_argument("--model", required=True); q.add_argument("--storage"); q.add_argument("--check", required=True, help="점검 JSON 파일"); q.add_argument("--today", required=True)
    l = s.add_parser("listing"); l.add_argument("--model", required=True); l.add_argument("--check", required=True); l.add_argument("--imei-checked", action="store_true"); l.add_argument("--factory-reset", action="store_true"); l.add_argument("--lost-stolen-clear", action="store_true")
    a = p.parse_args(argv)
    try:
        chk = json.load(open(a.check, encoding="utf-8")); gr = core.grade(chk)
        if a.cmd == "quote":
            est = core.estimate(core.load_comps(a.comps), a.model, date.fromisoformat(a.today), a.storage)
            if est["ok"]: print(f"시세 중앙값 {est['median']:,}원 (거래 {est['used']}건 사용, 이상치 {est['outliers']}건 제외, 범위 {est['low']:,}~{est['high']:,})")
            o = core.offer(est, gr); print(f"등급 {gr['grade']} · 수리비 {gr['repair']:,}원 · 예상 판매가 {o['resale']:,}원 → 매입 제안 {o['buy_offer']:,}원 (예상 이익 {o['expected_profit']:,}원)"); print(o["note"]); return 0
        t = core.listing(a.model, gr, chk, {"imei_checked": a.imei_checked, "factory_reset_done": a.factory_reset, "lost_stolen_clear": a.lost_stolen_clear}); print(t); return 0
    except (core.RefurbError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
