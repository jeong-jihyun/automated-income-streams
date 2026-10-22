import argparse
from datetime import datetime
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="noshow", description="예약 알림·대기자 채우기 (문자는 실제로 보내지 않고 화면에 출력)")
    p.add_argument("--db", default="noshow.db"); p.add_argument("--config", required=True)
    sub = p.add_subparsers(dest="cmd", required=True)
    a_ = sub.add_parser("add"); a_.add_argument("name"); a_.add_argument("phone"); a_.add_argument("slot")
    w = sub.add_parser("wait"); w.add_argument("name"); w.add_argument("phone"); w.add_argument("slot")
    r = sub.add_parser("remind"); r.add_argument("--now")
    y = sub.add_parser("reply"); y.add_argument("phone"); y.add_argument("text"); y.add_argument("--now")
    a = p.parse_args(argv)
    try:
        cfg = core.load_config(a.config); db = core.connect(a.db)
        now = datetime.strptime(a.now, core.FMT) if getattr(a, "now", None) else datetime.now()
        sender = lambda phone, text: print(f"  [문자 시험 출력] {phone}: {text}")
        if a.cmd == "add": print("예약 번호", core.add(db, a.name, a.phone, a.slot))
        elif a.cmd == "wait": print("대기 번호", core.join_waitlist(db, a.name, a.phone, a.slot))
        elif a.cmd == "remind":
            print(f"알림 {core.send_due(db, cfg, now, sender)}건"); core.expire_offers(db, cfg, now, sender)
        else: print("처리 결과:", core.handle_reply(db, cfg, a.phone, a.text, now, sender) or "알아듣지 못함")
        return 0
    except (core.NoshowError, ValueError) as e:
        print(f"[오류] {e}"); return 2
