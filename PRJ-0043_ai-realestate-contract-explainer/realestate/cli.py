import argparse
from . import analyze, registry, report


def main(argv=None):
    p = argparse.ArgumentParser(prog="realestate", description="등기부·계약서 글을 쉬운 말로 풀이 (전문가 자문 아님)")
    p.add_argument("registry", help="등기부 텍스트 파일"); p.add_argument("--price", type=int, help="집값(매매가·시세, 원)"); p.add_argument("--deposit", type=int, default=0, help="내 보증금(원)")
    p.add_argument("--landlord", help="계약서의 임대인 이름"); p.add_argument("--contract", help="계약서 특약 텍스트 파일"); p.add_argument("--out")
    a = p.parse_args(argv)
    try:
        res = analyze.analyze(registry.parse(open(a.registry, encoding="utf-8").read()), a.price, a.deposit, a.landlord)
        miss = analyze.special_terms(open(a.contract, encoding="utf-8").read()) if a.contract else None
        md = report.markdown(res, miss)
        open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md)
        return 0
    except (registry.RegError, OSError) as e:
        print(f"[오류] {e}"); return 2
