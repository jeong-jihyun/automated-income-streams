import argparse
from .batch import run
from .process import PRESETS, PhotoError
COLORS = {"white": (255, 255, 255), "gray": (240, 240, 240)}


def main(argv=None):
    p = argparse.ArgumentParser(prog="photobatch", description="상품 사진 배경을 단색으로 바꾸고 규격에 맞추기 (단순한 배경만)")
    p.add_argument("src"); p.add_argument("dst"); p.add_argument("--preset", default="square_1000", choices=list(PRESETS)); p.add_argument("--color", default="white", choices=list(COLORS)); p.add_argument("--dry-run", action="store_true")
    a = p.parse_args(argv)
    try: rows = run(a.src, a.dst, a.preset, COLORS[a.color], a.dry_run)
    except PhotoError as e:
        print(f"[오류] {e}"); return 2
    ok = sum(r["status"] == "ok" for r in rows)
    for r in rows:
        if r["status"] == "fail": print(f"실패: {r['file']} — {r['reason']}")
    print(f"완료 {ok}장 / 실패 {len(rows) - ok}장 / 전체 {len(rows)}장" + (" (dry-run: 저장 안 함)" if a.dry_run else ""))
    return 0 if rows else 1
