import argparse
from . import guide, load


def main(argv=None):
    p = argparse.ArgumentParser(prog="reviewsum", description="리뷰 CSV를 장단점 구매 가이드로 요약")
    p.add_argument("csv"); p.add_argument("--out"); p.add_argument("--affiliate", action="store_true", help="제휴 링크 표시 문구 추가")
    a = p.parse_args(argv)
    try:
        rows, skipped = load.load(a.csv)
        if skipped: print(f"[건너뜀] 읽을 수 없는 줄 {len(skipped)}개: {skipped[:5]}")
        md = guide.markdown(guide.build(rows, affiliate=a.affiliate))
        open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md)
        return 0
    except (load.ReviewError, ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
