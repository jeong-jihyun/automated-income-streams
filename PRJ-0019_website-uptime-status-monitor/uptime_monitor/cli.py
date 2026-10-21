import argparse
import os
import time
from datetime import datetime
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="uptime_monitor", description="내 사이트 가동 점검·상태 페이지 (본인 사이트만 점검하세요)")
    p.add_argument("--config", required=True); p.add_argument("--db", default="monitor.db"); p.add_argument("--page", default="status.html")
    p.add_argument("--loop", type=int, default=0, help="초 간격으로 계속 점검 (0이면 한 번만)")
    a = p.parse_args(argv)
    try:
        cfg = core.load_config(a.config)
    except core.MonitorError as e:
        print(f"[오류] {e}"); return 2
    db = core.connect(a.db)

    def notify(text):
        print(text)
        if cfg.get("webhook_url"):
            try:
                core.send_webhook(cfg["webhook_url"], text)
            except Exception as e:
                print(f"(웹훅 전송 실패: {e})")
    while True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for name, res, _ in core.run_once(db, cfg, now, notify):
            print(f"{name}: {'정상' if res['ok'] else '실패'} {res['ms']}ms {res['reason']}")
        open(a.page, "w", encoding="utf-8").write(core.status_page(db, cfg, now))
        if a.loop <= 0:
            return 0
        time.sleep(max(a.loop, 30))
