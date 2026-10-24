import argparse
import datetime
import json
from . import mbti, reading, saju, tarot


def main(argv=None):
    p = argparse.ArgumentParser(prog="fortune", description="사주·타로·MBTI 상담 (재미용, AI는 꽂아 쓰는 구조)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("mbti"); s.add_argument("questions"); s.add_argument("answers", help="쉼표로 구분한 1~5 숫자")
    s = sub.add_parser("tarot"); s.add_argument("--n", type=int, default=3); s.add_argument("--seed", type=int); s.add_argument("--question", default="")
    s = sub.add_parser("saju"); s.add_argument("birth", help="YYYY-MM-DD"); s.add_argument("--hour", type=int)
    a = p.parse_args(argv)
    try:
        if a.cmd == "mbti":
            r = mbti.score(json.load(open(a.questions, encoding="utf-8")), [int(x) for x in a.answers.split(",")])
            print(f"MBTI: {r['type']}" + ("" if r["complete"] else " (X는 점수가 같아 정하지 못한 축)") + f" / 축별 점수 {r['detail']}")
        elif a.cmd == "tarot":
            cards = tarot.draw(a.n, a.seed); res = reading.consult(a.question, cards)
            for c in cards: print(f"- {c['position']}: {c['card']}{'(거꾸로)' if c['reversed'] else ''} — {c['meaning']}")
            print(res["text"])
        else:
            pl = saju.pillars(datetime.date.fromisoformat(a.birth), a.hour)
            for k, v in pl.items(): print(f"{k}: {v['name']} ({v['hanja']})")
            print("오행:", saju.elements(pl), "\n월주는 구현하지 않았고 연주는 입춘을 2/4로 근사했습니다. " + "재미용입니다.")
        return 0
    except (mbti.FortuneError, ValueError, OSError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
