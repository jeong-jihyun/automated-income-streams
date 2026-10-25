import argparse
import json
from . import grammar, session


def main(argv=None):
    p = argparse.ArgumentParser(prog="tutor", description="영어 회화 연습 도우미(받아쓰기 결과 기준, 음성 인식은 꽂아 쓰는 구조)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check"); s.add_argument("text")
    s = sub.add_parser("drill"); s.add_argument("scenarios"); s.add_argument("--id", type=int, required=True); s.add_argument("--said", required=True); s.add_argument("--log")
    s = sub.add_parser("progress"); s.add_argument("log")
    a = p.parse_args(argv)
    try:
        if a.cmd == "check":
            r = grammar.check(a.text)
            for x in r: print(f"- [{x['rule']}] '{x['found']}' → '{x['suggest']}' : {x['ko']}")
            print("고칠 곳이 없어요." if not r else f"{len(r)}곳 점검했어요. (간이 규칙이라 놓치는 실수가 있어요)")
        elif a.cmd == "drill":
            sc = {x["id"]: x for x in json.load(open(a.scenarios, encoding="utf-8"))}
            if a.id not in sc: raise ValueError(f"없는 문장 번호: {a.id}")
            r = session.practice(sc[a.id]["target"], a.said)
            print(f"점수 {r['score']}점 — {r['grade']}")
            for t in r["tips"] + [f"[{g['rule']}] {g['ko']}" for g in r["grammar"]]: print("-", t)
            if a.log: session.log(a.log, r)
        else:
            r = session.progress(a.log); print("기록이 없어요." if not r["count"] else f"{r['count']}번 연습, 평균 {r['avg']}점, 날짜별 {r['days']}")
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
