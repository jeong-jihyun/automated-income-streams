import argparse
import datetime
from . import estimate, log, nutrition, photo


def main(argv=None):
    p = argparse.ArgumentParser(prog="foodcal", description="음식 칼로리 대략 추정(사진 인식은 꽂아 쓰는 구조, 목표·식단 조언 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check-photo"); s.add_argument("path")
    s = sub.add_parser("estimate"); s.add_argument("--item", action="append", required=True, help="음식=양 (예: 쌀밥=M, 김치=30g)"); s.add_argument("--log"); s.add_argument("--meal", default="식사"); s.add_argument("--date")
    s = sub.add_parser("day"); s.add_argument("log"); s.add_argument("--date")
    a = p.parse_args(argv)
    try:
        if a.cmd == "check-photo":
            r = photo.check_photo(a.path); print("사진 좋아요" if r["ok"] else "다시 찍어 주세요: " + ", ".join(r["problems"]))
        elif a.cmd == "estimate":
            items = []
            for x in a.item:
                if "=" not in x: raise nutrition.FoodError(f"형식은 음식=양: {x}")
                l, q = x.split("=", 1); items.append((l.strip(), q.strip(), 1.0))
            res = estimate.estimate(items); print(estimate.text(res))
            if a.log: log.add(a.log, a.date or datetime.date.today().isoformat(), a.meal, res)
        else:
            r = log.day(a.log, a.date or datetime.date.today().isoformat()); print(f"끼니 {len(r['meals'])}개, 합계 대략 {r['kcal']}kcal (범위 {r['low']}~{r['high']})")
        return 0
    except (nutrition.FoodError, OSError) as e:
        print(f"[오류] {e}"); return 2
