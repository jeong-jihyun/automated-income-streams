import argparse
import time
from . import core, server


def main(argv=None):
    p = argparse.ArgumentParser(prog="form_backend", description="정적 사이트용 폼·댓글 백엔드 (시험용 로컬 서버)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("--config", required=True)
    s = sub.add_parser("serve"); s.add_argument("--config", required=True); s.add_argument("--db", default="forms.db"); s.add_argument("--port", type=int, default=8100)
    a = p.parse_args(argv)
    try:
        cfg = core.load_config(a.config)
    except core.BackendError as e:
        print(f"[오류] {e}"); return 2
    print(f"설정 확인: 사이트 {', '.join(cfg['sites'])}")
    if a.cmd == "serve":
        print(f"시험용 서버 http://127.0.0.1:{a.port} (HTTPS·도메인 없이 인터넷에 열지 마세요) — Ctrl+C로 끔")
        notifier = lambda site, form, data: print(f"[알림 시험 출력] {site}/{form}: {list(data)}")
        server.serve(core.Backend(cfg, core.connect(a.db), time.time, notifier), a.port)
    return 0
