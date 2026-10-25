import argparse
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="digest", description="관심 종목 공시·뉴스 제목 알림 (투자 자문 아님, 직접 수집 없음)")
    p.add_argument("items", help="항목 JSON 파일"); p.add_argument("--watch", default="", help="관심 종목명(쉼표). 비우면 전체")
    p.add_argument("--state", help="이미 보낸 항목 기록 파일"); p.add_argument("--min", type=int, default=1, choices=[1, 2, 3]); p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    try:
        recs, skip, sent = core.run(core.load_items(a.items), [w.strip() for w in a.watch.split(",") if w.strip()], a.state, print, a.min, a.dry_run)
    except core.DigestError as e:
        print(f"[오류] {e}"); return 2
    if a.dry_run: print(core.render(recs))
    print(f"(건너뜀: 이미 보냄 {skip['already_sent']}, 중복 {skip['duplicate']}, 관심 아님 {skip['not_watched']}, 중요도 낮음 {skip['low']})")
    return 0
