import argparse, csv, json
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="bulklist", description="상품 목록(엑셀·CSV) 검수와 정리 CSV 내보내기 (업로드 없음)")
    p.add_argument("file"); p.add_argument("--categories", required=True, help="허용 카테고리 코드 JSON(목록)"); p.add_argument("--out", help="통과한 상품만 내보낼 CSV"); p.add_argument("--errors", help="오류 목록 CSV")
    a = p.parse_args(argv)
    try:
        cats = set(json.load(open(a.categories, encoding="utf-8"))); r = core.run(a.file, cats)
        for u in r["unknown_columns"]: print(f"[알림] 모르는 열은 무시했어요: {u}")
        for e in r["errors"]: print(f"{e['row']}행 [{e['col']}] {e['msg']}")
        if a.errors:
            with open(a.errors, "w", newline="", encoding="utf-8-sig") as f: w = csv.DictWriter(f, fieldnames=["row", "col", "msg"]); w.writeheader(); w.writerows(r["errors"])
        if a.out: core.export(r["good"], a.out)
        print(f"전체 {r['total']}개 중 통과 {len(r['good'])}개 / 오류 {r['bad_rows']}개 행 (업로드는 하지 않았어요)"); return 0 if not r["errors"] else 1
    except (core.ListError, OSError, ValueError) as e:
        print(f"[오류] {e}"); return 2
