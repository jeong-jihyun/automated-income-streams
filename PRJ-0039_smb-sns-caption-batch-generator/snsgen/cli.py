import argparse
import csv
from . import generate, store


def main(argv=None):
    p = argparse.ArgumentParser(prog="snsgen", description="소상공인 SNS 글 한 달 치 만들기 (올리기는 직접, 자동 게시 없음)")
    p.add_argument("shop"); p.add_argument("--start", required=True); p.add_argument("--days", type=int, default=30); p.add_argument("--seed", type=int, default=1); p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        s = store.load(a.shop); posts = generate.generate(s, a.start, a.days, a.seed)
        with open(a.out, "w", encoding="utf-8-sig", newline="") as f: csv.writer(f).writerows(generate.to_csv_rows(posts))
        bad, rep = sum(1 for x in posts if x["problems"]), sum(1 for x in posts if x["repeat"])
        print(f"[완료] {len(posts)}개 글 → {a.out}" + (f" (점검 필요 {bad}개)" if bad else "") + (f" · 틀이 모자라 똑같은 글 {rep}개 (상품·이벤트를 더 적어 주세요)" if rep else ""))
        return 0
    except (store.SnsError, ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
