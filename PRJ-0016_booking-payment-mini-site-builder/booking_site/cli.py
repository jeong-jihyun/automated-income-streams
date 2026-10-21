import argparse
import os
from . import config, engine, site, server


def main(argv=None):
    p = argparse.ArgumentParser(prog="booking_site", description="예약·시험결제 미니 사이트 (실제 결제 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    for n in ("check", "build", "serve"):
        s = sub.add_parser(n); s.add_argument("--config", required=True)
        if n == "build": s.add_argument("--out", required=True)
        if n == "serve": s.add_argument("--port", type=int, default=8000); s.add_argument("--db", default=":memory:")
    a = p.parse_args(argv)
    try:
        cfg = config.load(a.config)
        print(f"설정 확인 완료: {cfg['shop_name']} / 서비스 {len(cfg['services'])}개 / 하루 {len(engine.slots_for(cfg, '2030-01-01'))}칸")
        if a.cmd == "build":
            os.makedirs(a.out, exist_ok=True)
            open(os.path.join(a.out, "index.html"), "w", encoding="utf-8").write(site.build_page(cfg))
            print(f"[완료] {a.out}/index.html (소개 페이지만. 예약 기능은 serve 로 시험)")
        elif a.cmd == "serve":
            print(f"시험용 서버 http://127.0.0.1:{a.port}  (끄려면 Ctrl+C) — 결제는 시험용입니다")
            server.serve(cfg, engine.connect(a.db), a.port)
        return 0
    except config.ConfigError as e:
        print(f"[오류] {e}")
        return 2
