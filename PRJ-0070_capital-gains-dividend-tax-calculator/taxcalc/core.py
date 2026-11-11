"""거래 내역 CSV로 연도별 양도차익(선입선출)과 배당소득을 계산해 예상 세금을 보여 준다. 세율·공제는 설정(예시)이며 실제 세법과 다를 수 있음."""
import csv, datetime as dt
from collections import defaultdict, deque

CFG = {"overseas_deduction": 2_500_000, "overseas_rate": 0.22, "domestic_listed_taxed": False, "dividend_withhold_rate": 0.154, "financial_income_threshold": 20_000_000}
TYPES = {"buy", "sell", "dividend"}


def read(path):
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        need = {"date", "type", "symbol", "market", "qty", "price"}
        if rd.fieldnames is None or need - set(rd.fieldnames): raise ValueError("필수 열이 없습니다: " + ", ".join(sorted(need - set(rd.fieldnames or []))))
        for i, r in enumerate(rd, start=2):
            try:
                t = r["type"].strip().lower()
                if t not in TYPES: raise ValueError(f"type은 buy/sell/dividend 중 하나")
                m = r["market"].strip().lower()
                if m not in ("domestic", "overseas"): raise ValueError("market은 domestic/overseas 중 하나")
                row = {"date": dt.date.fromisoformat(r["date"].strip()), "type": t, "symbol": r["symbol"].strip(), "market": m,
                       "qty": float(r["qty"] or 0), "price": float(r["price"]), "fee": float(r.get("fee") or 0), "fx": float(r.get("fx") or 1),
                       "withheld": (float(r["withheld"]) if (r.get("withheld") or "").strip() else None)}
                if row["price"] < 0 or row["fee"] < 0 or row["fx"] <= 0 or (t != "dividend" and row["qty"] <= 0): raise ValueError("수량·가격·수수료·환율 값 오류")
            except (ValueError, TypeError, KeyError) as e:
                raise ValueError(f"{i}행: {e}")
            rows.append(row)
    return sorted(rows, key=lambda x: (x["date"], 0 if x["type"] == "buy" else 1))


def compute(rows, cfg=None):
    c = dict(CFG); c.update(cfg or {})
    lots = defaultdict(deque)                      # (market, symbol) -> [수량, 1주당 취득가(수수료 포함, 원화)]
    gains = defaultdict(lambda: {"domestic": 0.0, "overseas": 0.0}); divs = defaultdict(lambda: {"gross": 0.0, "withheld": 0.0}); sells = []
    for r in rows:
        k = (r["market"], r["symbol"]); y = r["date"].year
        if r["type"] == "buy":
            lots[k].append([r["qty"], (r["price"] * r["fx"]) + r["fee"] * r["fx"] / r["qty"]])
        elif r["type"] == "sell":
            have = sum(l[0] for l in lots[k])
            if r["qty"] > have + 1e-9: raise ValueError(f"{r['date']} {r['symbol']}: 보유 {have:g}주보다 많은 {r['qty']:g}주를 팔았습니다 (매수 내역 누락?)")
            left, cost = r["qty"], 0.0
            while left > 1e-9:
                l = lots[k][0]; take = min(left, l[0]); cost += take * l[1]; l[0] -= take; left -= take
                if l[0] <= 1e-9: lots[k].popleft()
            proceeds = r["qty"] * r["price"] * r["fx"] - r["fee"] * r["fx"]
            g = proceeds - cost; gains[y][r["market"]] += g; sells.append((r["date"], r["symbol"], r["market"], round(g)))
        else:
            gross = (r["qty"] if r["qty"] else 1) * r["price"] * r["fx"]
            wh = r["withheld"] * r["fx"] if r["withheld"] is not None else gross * c["dividend_withhold_rate"]
            divs[y]["gross"] += gross; divs[y]["withheld"] += wh
    out = {}
    for y in sorted(set(gains) | set(divs)):
        ov, dm = gains[y]["overseas"], gains[y]["domestic"]
        taxable = max(ov - c["overseas_deduction"], 0); tax_ov = taxable * c["overseas_rate"]
        tax_dm = max(dm, 0) * c["overseas_rate"] if c["domestic_listed_taxed"] else 0
        d = divs[y]; w = []
        if d["gross"] > c["financial_income_threshold"]: w.append("배당 등 금융소득이 종합과세 기준(예시)을 넘음 - 세무 전문가 확인 필요")
        if ov < 0: w.append("해외 주식 손실 - 이 도구는 다음 해로 이월하지 않음(해외주식 손실은 이월되지 않는 것으로 알려져 있으나 확인 필요)")
        out[y] = {"overseas_gain": round(ov), "domestic_gain": round(dm), "overseas_taxable": round(taxable), "overseas_tax": round(tax_ov),
                  "domestic_tax": round(tax_dm), "div_gross": round(d["gross"]), "div_withheld": round(d["withheld"]), "warnings": w}
    return out, sells, {k: [list(l) for l in v] for k, v in lots.items() if v}


def text(res, sells):
    L = []
    for y, r in res.items():
        L.append(f"[{y}년] 해외 양도차익 {r['overseas_gain']:,}원 → 공제 후 과세표준 {r['overseas_taxable']:,}원 → 예상 양도세 {r['overseas_tax']:,}원")
        L.append(f"        국내 상장주식 양도차익 {r['domestic_gain']:,}원 (예상 세금 {r['domestic_tax']:,}원), 배당 {r['div_gross']:,}원 (원천징수 {r['div_withheld']:,}원)")
        L += ["        주의: " + w for w in r["warnings"]]
    L.append("※ 세율·공제·과세 대상은 예시 설정값이고 실제 신고 금액이 아닙니다. 환율은 입력값이며, 취득가는 선입선출로 계산했습니다. 세무 상담이 아닙니다.")
    return "\n".join(L)
