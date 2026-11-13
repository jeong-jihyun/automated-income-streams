import argparse, json, os, sys
from . import core


def main(argv=None):
    p = argparse.ArgumentParser(prog="quoteinv", description="견적서·청구서 HTML 만들기 (세금계산서 발행 아님)")
    p.add_argument("spec"); p.add_argument("--out", default="out")
    a = p.parse_args(argv)
    try:
        d = core.load(a.spec); c = core.calc(d)
        os.makedirs(a.out, exist_ok=True)
        reg = os.path.join(a.out, "numbers.json")
        used = json.load(open(reg, encoding="utf-8")) if os.path.exists(reg) else []
        num = core.next_number(d["type"], d["date"], used)
        path = os.path.join(a.out, num + ".html")
        open(path, "w", encoding="utf-8").write(core.render(d, num, c))
        json.dump(used + [num], open(reg, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"{num}: 공급가액 {c['supply']:,} / 부가세 {c['vat']:,} / 합계 {c['total']:,}원 → {path}")
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print("오류:", e, file=sys.stderr); return 2
    return 0
