import argparse
import json
from . import planner


def main(argv=None):
    p = argparse.ArgumentParser(prog="tripplan", description="취향·예산에 맞춘 여행 일정표 만들기")
    p.add_argument("places", help="장소 JSON"); p.add_argument("--days", type=int, required=True); p.add_argument("--budget", type=int, required=True)
    p.add_argument("--interests", default=""); p.add_argument("--pace", default="normal"); p.add_argument("--out")
    a = p.parse_args(argv)
    try:
        places = json.load(open(a.places, encoding="utf-8"))
        r = planner.plan(places, a.days, a.budget, [x.strip() for x in a.interests.split(",") if x.strip()], a.pace)
        md = planner.render(r, a.budget)
        open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md)
        return 0
    except (planner.PlanError, OSError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
