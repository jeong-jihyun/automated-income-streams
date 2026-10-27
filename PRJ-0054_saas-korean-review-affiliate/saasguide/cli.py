import argparse
from datetime import date
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="saasguide", description="해외 SaaS 한국어 가이드 초안/점검 (직접 써 본 경우만, 자동 게시 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    m = s.add_parser("make"); m.add_argument("facts"); m.add_argument("--out"); m.add_argument("--today")
    c = s.add_parser("check"); c.add_argument("text")
    a = p.parse_args(argv)
    try:
        if a.cmd == "make":
            t = core.make(core.load(a.facts), date.fromisoformat(a.today) if a.today else None); open(a.out, "w", encoding="utf-8").write(t) if a.out else print(t); return 0
        r = core.check(open(a.text, encoding="utf-8").read())
        for k, msg in r: print(f"[{k}] {msg}")
        print("통과" if not r else f"문제 {len(r)}개"); return 0 if not r else 1
    except (core.GuideError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
