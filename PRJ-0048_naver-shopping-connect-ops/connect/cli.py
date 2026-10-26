import argparse
from . import post


def main(argv=None):
    p = argparse.ArgumentParser(prog="connect", description="상품 후기 글 초안/점검 (직접 써 본 경험이 있어야 초안 생성, 자동 게시 없음)")
    s = p.add_subparsers(dest="cmd", required=True)
    m = s.add_parser("make"); m.add_argument("facts"); m.add_argument("--out")
    c = s.add_parser("check"); c.add_argument("text"); c.add_argument("--photos", type=int, default=0)
    a = p.parse_args(argv)
    try:
        if a.cmd == "make":
            t = post.make(post.load(a.facts)); open(a.out, "w", encoding="utf-8").write(t) if a.out else print(t); return 0
        r = post.check(open(a.text, encoding="utf-8").read(), a.photos)
        for k, m_ in r: print(f"[{k}] {m_}")
        print("통과" if not r else f"문제 {len(r)}개"); return 0 if not r else 1
    except (post.PostError, OSError) as e:
        print(f"[오류] {e}"); return 2
