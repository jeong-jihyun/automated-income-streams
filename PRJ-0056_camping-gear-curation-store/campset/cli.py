import argparse
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="campset", description="캠핑·차박 세트 구성기 (재고·수용 인원·보온 등급·마진 확인)")
    p.add_argument("catalog"); p.add_argument("--persons", type=int, required=True); p.add_argument("--season", required=True); p.add_argument("--mode", default="캠핑"); p.add_argument("--budget", type=int, required=True); p.add_argument("--min-margin", type=float, default=10)
    a = p.parse_args(argv)
    try:
        r = core.build(core.load(a.catalog), a.persons, a.season, a.mode, a.budget, a.min_margin); print(core.render(r, a.persons, a.season, a.mode, a.budget)); return 0 if r["ok"] else 1
    except core.SetError as e:
        print(f"[오류] {e}"); return 2
