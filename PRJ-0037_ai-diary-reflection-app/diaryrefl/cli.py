import argparse
import datetime
from . import reflect, store, summary


def main(argv=None):
    p = argparse.ArgumentParser(prog="diaryrefl", description="일기 기록·요약·회고 (AI는 꽂아 쓰는 구조, 진단 아님)")
    p.add_argument("--file", default="diary.json")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add"); s.add_argument("body"); s.add_argument("--date"); s.add_argument("--mood", type=int)
    s = sub.add_parser("summary"); s.add_argument("date"); s.add_argument("--k", type=int, default=2)
    s = sub.add_parser("reflect"); s.add_argument("start"); s.add_argument("end")
    a = p.parse_args(argv)
    try:
        d = store.load(a.file)
        if a.cmd == "add":
            store.save(a.file, store.add(d, a.date or datetime.date.today().isoformat(), a.body, a.mood)); print("[완료] 저장")
            if any(c in a.body for c in reflect.CRISIS): print(reflect.CRISIS_MSG)
        elif a.cmd == "summary":
            e = [x for x in d if x["date"] == a.date]
            if not e: raise store.DiaryError(f"{a.date} 기록이 없습니다")
            print("\n".join(summary.summarize(e[0]["body"], a.k)))
        else:
            print(reflect.reflect(d, a.start, a.end)["text"])
        return 0
    except (store.DiaryError, ValueError) as e:
        print(f"[오류] {e}"); return 2
