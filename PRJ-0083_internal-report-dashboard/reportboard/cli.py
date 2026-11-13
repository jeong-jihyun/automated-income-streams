import argparse, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="reportboard", description="팀별 보고 CSV 폴더 → HTML 대시보드")
    p.add_argument("folder"); p.add_argument("--out", default="dashboard.html"); p.add_argument("--teams", default="", help="보고해야 하는 팀(쉼표)")
    a = p.parse_args(argv)
    try:
        rows, bad = core.read_dir(a.folder)
        if not rows:
            raise ValueError("읽을 수 있는 줄이 없습니다")
        d, dup = core.merge(rows)
        s = core.summarize(d, [t.strip() for t in a.teams.split(",") if t.strip()])
        open(a.out, "w", encoding="utf-8").write(core.render(s, bad))
        print(f"{s['week']} 기준 {len(s['teams'])}개 팀, 지표 {len(s['table'])}개 → {a.out} (제외 {len(bad)}줄, 중복 덮어씀 {dup}건)")
    except (OSError, ValueError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
