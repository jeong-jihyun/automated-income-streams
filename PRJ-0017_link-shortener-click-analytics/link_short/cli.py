import argparse
from datetime import datetime
from . import core, server


def main(argv=None):
    p = argparse.ArgumentParser(prog="link_short", description="링크 단축·클릭 분석 (시험용 로컬 서버)")
    p.add_argument("--db", default="links.db")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("add"); c.add_argument("url"); c.add_argument("--code")
    s = sub.add_parser("stats"); s.add_argument("code"); s.add_argument("--include-bots", action="store_true")
    v = sub.add_parser("serve"); v.add_argument("--port", type=int, default=8080)
    a = p.parse_args(argv)
    db = core.connect(a.db)
    try:
        if a.cmd == "add":
            print("코드:", core.create(db, a.url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), a.code))
        elif a.cmd == "stats":
            st = core.stats(db, a.code, not a.include_bots)
            print(f"클릭 {st['total']}회 (봇 제외 {st['bots_excluded']}회)")
            for k, t in (("by_day", "날짜별"), ("by_source", "유입 경로"), ("by_device", "기기"), ("by_utm", "utm_source")):
                print(f" {t}: " + ", ".join(f"{x} {n}" for x, n in st[k]))
        else:
            print(f"시험용 서버 http://127.0.0.1:{a.port}/<코드>  (Ctrl+C로 끔)")
            server.serve(db, a.port)
        return 0
    except core.LinkError as e:
        print(f"[오류] {e}")
        return 2
