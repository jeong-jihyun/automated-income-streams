"""구매 가이드: 별점 분포, 항목별 장단점(근거 개수와 실제 리뷰 한 줄), 의심 리뷰 수, 제휴 표시."""
from collections import Counter
from . import aspects, fake

DISCLAIMER = "※ 리뷰에서 자주 나온 말을 센 요약이며 제품의 품질을 보증하지 않습니다. 의심 리뷰는 규칙으로 표시한 것일 뿐 가짜라고 단정할 수 없습니다."
AFFILIATE = "※ 이 가이드의 구매 링크는 제휴 링크일 수 있으며, 구매 시 운영자가 수수료를 받을 수 있습니다."


def build(rows, min_support=2, affiliate=False):
    marked = fake.flag(rows)
    ok = [r for r in marked if not r["suspect"]]; sus = [r for r in marked if r["suspect"]]
    if not ok: raise ValueError("의심 리뷰를 빼면 남는 리뷰가 없습니다")
    dist = Counter(r["rating"] for r in ok)
    asp = aspects.analyze(ok)
    pros = [(a, len(v["good"]), v["good"][0]) for a, v in asp.items() if len(v["good"]) >= min_support and len(v["good"]) > len(v["bad"])]
    cons = [(a, len(v["bad"]), v["bad"][0]) for a, v in asp.items() if len(v["bad"]) >= min_support and len(v["bad"]) >= len(v["good"])]
    pros.sort(key=lambda x: -x[1]); cons.sort(key=lambda x: -x[1])
    return {"total": len(rows), "used": len(ok), "suspect": len(sus), "avg": round(sum(r["rating"] for r in ok) / len(ok), 2), "dist": {i: dist.get(i, 0) for i in range(5, 0, -1)},
            "pros": pros, "cons": cons, "affiliate": affiliate}


def markdown(g):
    o = ["# 구매 가이드", "", f"리뷰 {g['total']}개 중 {g['used']}개로 계산 (의심 리뷰 {g['suspect']}개 제외) · 평균 별점 {g['avg']}", "",
         "별점 분포: " + " · ".join(f"{k}점 {v}" for k, v in g["dist"].items()), "", "## 좋다는 의견"]
    o += [f"- **{a}** ({n}명) — \"{q[:50]}\"" for a, n, q in g["pros"]] or ["- (뚜렷한 장점 의견 없음)"]
    o += ["", "## 아쉽다는 의견"] + ([f"- **{a}** ({n}명) — \"{q[:50]}\"" for a, n, q in g["cons"]] or ["- (뚜렷한 단점 의견 없음)"])
    o += ["", DISCLAIMER] + ([AFFILIATE] if g["affiliate"] else [])
    return "\n".join(o) + "\n"
