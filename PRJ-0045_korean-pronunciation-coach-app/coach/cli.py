import argparse, sys
from .compare import compare


def main(argv=None):
    p = argparse.ArgumentParser(prog="coach", description="한국어 발음 연습: 목표 문장과 인식된 글 비교")
    p.add_argument("target", help="목표 문장"); p.add_argument("heard", help="음성인식기가 받아 적은 글")
    a = p.parse_args(argv)
    try: r = compare(a.target, a.heard)
    except ValueError as e:
        print(f"[오류] {e}"); return 2
    print(f"소리 나는 대로: {r['target_sound']}  (간이 규칙)")
    if r["empty"]: print("인식된 글이 없어요. 조용한 곳에서 다시 말해 보세요."); print(r["note"]); return 0
    print(f"일치도: {r['score']}점")
    for d in r["diffs"]:
        print(f"- {d['kind']}: 목표 '{d['want']}' ↔ 인식 '{d['got']}'" + (f"\n  팁: {d['tip']}" if d["tip"] else "") + (f"\n  Tip: {d['tip_en']}" if d["tip_en"] else ""))
    if not r["diffs"]: print("잘 읽었어요!")
    print(r["note"]); return 0
