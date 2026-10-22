import argparse
import json
import os
from datetime import datetime
from . import posts, replies


def main(argv=None):
    p = argparse.ArgumentParser(prog="insta_tool", description="인스타그램 예약 목록 점검·댓글 답변 계획 (실제 게시/발행은 하지 않음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check"); c.add_argument("--csv", required=True)
    d = sub.add_parser("due"); d.add_argument("--csv", required=True); d.add_argument("--now"); d.add_argument("--done", default="")
    r = sub.add_parser("replies"); r.add_argument("--rules", required=True); r.add_argument("--comments", required=True, help='JSON: [{"id","user","text"}]')
    a = p.parse_args(argv)
    try:
        if a.cmd == "replies":
            cfg = replies.load_rules(a.rules); comments = json.load(open(a.comments, encoding="utf-8"))
            for x in replies.plan(cfg, comments):
                print(f"#{x['id']} {x['action']}: {x['reason']}" + (f" → {x['reply']}" if x.get("reply") else ""))
            print("※ 위 답변은 후보입니다. 사람이 확인한 뒤 직접 올리세요.")
            return 0
        rows = posts.load(a.csv); base = os.path.dirname(os.path.abspath(a.csv))
        if a.cmd == "check":
            probs = posts.check(rows, base)
            for i, m in probs: print(f" - {i}행: {m}")
            for x, y in posts.find_conflicts(rows): print(f" - 게시물 {x}와 {y}가 1시간 안에 겹칩니다")
            print(f"점검 완료: {len(rows)}건 / 문제 {len(probs)}건")
            return 1 if probs else 0
        now = datetime.strptime(a.now, "%Y-%m-%d %H:%M") if a.now else datetime.now()
        for r_ in posts.due(rows, now, set(filter(None, a.done.split(",")))):
            print(f"올릴 차례: #{r_['id']} {r_['when']} {r_['image']}")
        return 0
    except (posts.PostError, replies.RuleError, FileNotFoundError, ValueError) as e:
        print(f"[오류] {e}")
        return 2
