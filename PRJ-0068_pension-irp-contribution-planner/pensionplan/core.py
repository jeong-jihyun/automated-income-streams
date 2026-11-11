"""은퇴 목표에 필요한 월 적립액과 세액공제 예상액 계산. 세법 기준값은 설정(예시)이며 현재 법과 다를 수 있음."""
import math

CFG = {"credit_limit_total": 9_000_000, "credit_limit_pension": 6_000_000, "credit_rate_low": 0.165, "credit_rate_high": 0.132,
       "salary_split": 55_000_000, "pension_start_age": 55}


def check(p):
    err = []
    for k in ("age", "retire_age", "life_age", "salary", "balance", "monthly_now", "return_rate", "post_return_rate", "inflation", "target_monthly_today"):
        if k not in p or not isinstance(p[k], (int, float)): err.append(f"{k}가 없거나 숫자가 아닙니다")
    if err: raise ValueError("; ".join(err))
    if not p["age"] < p["retire_age"] < p["life_age"]: err.append("나이는 현재 < 은퇴 < 기대수명 순이어야 합니다")
    if min(p["salary"], p["balance"], p["monthly_now"], p["target_monthly_today"]) < 0: err.append("금액은 0 이상이어야 합니다")
    if p["target_monthly_today"] == 0: err.append("목표 월 연금이 0입니다")
    if err: raise ValueError("; ".join(err))


def mrate(annual):
    return (1 + annual) ** (1 / 12) - 1


def fv_factor(r, n):          # 매월 1원씩 n개월 적립한 값의 미래가치
    return n if abs(r) < 1e-12 else ((1 + r) ** n - 1) / r


def pv_factor(r, n):          # 매월 1원씩 n개월 받기 위해 필요한 현재 금액
    return n if abs(r) < 1e-12 else (1 - (1 + r) ** -n) / r


def plan(p, cfg=None):
    c = dict(CFG); c.update(cfg or {}); check(p)
    n = round((p["retire_age"] - p["age"]) * 12); pay_n = round((p["life_age"] - p["retire_age"]) * 12)
    r, rp = mrate(p["return_rate"]), mrate(p["post_return_rate"])
    target_then = p["target_monthly_today"] * (1 + p["inflation"]) ** (p["retire_age"] - p["age"])
    need = target_then * pv_factor(rp, pay_n)
    grow = p["balance"] * (1 + r) ** n
    now_fv = grow + p["monthly_now"] * fv_factor(r, n)
    gap = max(need - grow, 0)
    required = gap / fv_factor(r, n)
    rate = c["credit_rate_low"] if p["salary"] <= c["salary_split"] else c["credit_rate_high"]
    annual = required * 12
    credit = min(annual, c["credit_limit_total"]) * rate
    w = []
    if p["retire_age"] < c["pension_start_age"]: w.append(f"은퇴 나이가 연금 개시 가능 나이({c['pension_start_age']}세)보다 어림 - 중간에 받으면 불이익 가능")
    if annual > c["credit_limit_total"]: w.append(f"필요 적립액이 연 세액공제 한도({c['credit_limit_total']:,}원)를 넘음 - 초과분은 공제 안 됨")
    if p["return_rate"] > 0.10: w.append("기대 수익률이 10%를 넘음 - 낙관적인 가정")
    if p["post_return_rate"] > p["return_rate"]: w.append("은퇴 후 수익률이 적립 기간보다 높게 가정됨")
    return {"months": n, "pay_months": pay_n, "target_then": round(target_then), "need": round(need), "fv_now": round(now_fv),
            "shortfall": round(max(need - now_fv, 0)), "required_monthly": math.ceil(required), "extra_monthly": max(math.ceil(required) - p["monthly_now"], 0),
            "credit_rate": rate, "credit": round(credit), "warnings": w}


def scenarios(p, cfg=None):
    out = []
    for d in (-0.02, 0.0, 0.02):
        q = dict(p, return_rate=max(p["return_rate"] + d, -0.5)); out.append((d, plan(q, cfg)["required_monthly"]))
    return out


def text(p, r):
    L = [f"은퇴까지 {r['months'] // 12}년, 받는 기간 {r['pay_months'] // 12}년",
         f"은퇴 시점 목표 월 연금: {r['target_then']:,}원 (물가상승 반영) → 필요한 자금 {r['need']:,}원",
         f"지금 방식 유지 시 예상 자금 {r['fv_now']:,}원 → 부족 {r['shortfall']:,}원",
         f"목표 달성에 필요한 월 적립액: {r['required_monthly']:,}원 (지금보다 {r['extra_monthly']:,}원 더)",
         f"예상 세액공제(예시 세율 {r['credit_rate']:.1%}): 연 {r['credit']:,}원"]
    L += ["주의: " + w for w in r["warnings"]]
    L.append("수익률이 2%p 다르면 월 적립액: " + ", ".join(f"{d:+.0%} → {v:,}원" for d, v in scenarios(p)))
    L.append("※ 세액공제 한도·세율·연금 개시 나이는 예시 설정값이고, 수익률은 가정일 뿐입니다. 세무·투자 상담이 아닙니다.")
    return "\n".join(L)
