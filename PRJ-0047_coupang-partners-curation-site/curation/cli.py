import argparse
from datetime import date
from . import site


def main(argv=None):
    p = argparse.ArgumentParser(prog="curation", description="주제별 추천 정적 사이트 만들기 (제휴 고지 자동 삽입, 쿠팡 정보 수집 없음)")
    p.add_argument("products"); p.add_argument("out"); p.add_argument("--today", help="기준 날짜 YYYY-MM-DD(시험용)")
    a = p.parse_args(argv)
    try: r = site.build(site.load(a.products), a.out, date.fromisoformat(a.today) if a.today else None)
    except (site.CurationError, ValueError) as e:
        print(f"[오류] {e}"); return 2
    for b in r["rejected"]: print(f"제외: {b['id']} — {'; '.join(b['errors'])}")
    print(f"페이지 {r['pages']}개, 상품 {r['included']}개 포함, {len(r['rejected'])}개 제외"); return 0
