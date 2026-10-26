import argparse, json
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="reviewblog", description="맛집·카페 후기 초안/점검/목차 (방문 메모 기반, 자동 게시 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    m = s.add_parser("make"); m.add_argument("visit"); m.add_argument("--out"); m.add_argument("--today")
    c = s.add_parser("check"); c.add_argument("text"); c.add_argument("--photos", type=int, default=0); c.add_argument("--sponsored", action="store_true")
    i = s.add_parser("index"); i.add_argument("visits")
    a = p.parse_args(argv)
    try:
        if a.cmd == "make":
            t = core.make(core.load(a.visit), date.fromisoformat(a.today) if a.today else None); open(a.out, "w", encoding="utf-8").write(t) if a.out else print(t); return 0
        if a.cmd == "index": print(core.index(core.load(a.visits))); return 0
        r = core.check(open(a.text, encoding="utf-8").read(), a.photos, a.sponsored)
        for k, msg in r: print(f"[{k}] {msg}")
        print("통과" if not r else f"문제 {len(r)}개"); return 0 if not r else 1
    except (core.ReviewError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
