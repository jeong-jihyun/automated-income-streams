"""요금제 비교: 사용량에 맞는 요금제만 걸러 월 실부담액·약정 기간 총액으로 정렬한다. 요금·할인율은 사용자가 넣은 자료(예시 값)이며 실제 요금이 아니다."""
import json
from datetime import date

STALE_DAYS = 30
DISCLOSURE = "※ 가입 연결 시 제휴사로부터 수수료를 받을 수 있습니다. 요금·혜택은 입력된 자료 기준이며 가입 전 통신사에서 다시 확인하세요."


class PlanError(ValueError):
    pass


def load(path):
    try: d = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise PlanError(f"요금제 파일을 읽지 못했습니다: {e}")
    for i, p in enumerate(d):
        for k in ("id", "carrier", "name", "monthly", "price_date"):
            if p.get(k) in (None, ""): raise PlanError(f"{i + 1}번째 요금제에 '{k}'가 없습니다")
        if p["monthly"] < 0: raise PlanError(f"{p['id']}: 월 요금이 음수입니다")
    return d


def fits(plan, need_gb, need_call):
    gb = plan.get("data_gb")               # None = 무제한
    if need_gb is not None and gb is not None and gb < need_gb: return False
    return plan.get("call", "unlimited") == "unlimited" or (plan["call"] >= need_call)


def cost(plan, discount=0.0, device_monthly=0, months=24):
    eff = round(plan["monthly"] * (1 - discount)) + device_monthly
    return {"monthly": eff, "total": eff * months}


def rank(plans, need_gb=None, need_call=0, discount=0.0, device_monthly=0, months=24, today=None):
    today = today or date.today(); out = []
    for p in plans:
        if not fits(p, need_gb, need_call): continue
        c = cost(p, discount, device_monthly, months); age = (today - date.fromisoformat(p["price_date"])).days
        out.append({**p, **c, "age_days": age, "stale": age > STALE_DAYS})
    return sorted(out, key=lambda x: (x["total"], x["name"]))


def render(ranked, months=24):
    if not ranked: return "조건에 맞는 요금제가 없어요.\n\n" + DISCLOSURE
    lines = ["| 순위 | 통신사 | 요금제 | 월 실부담 | " + f"{months}개월 합계 | 데이터 | 확인일 |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(ranked, 1):
        d = "무제한" if r.get("data_gb") is None else f"{r['data_gb']}GB"
        lines.append(f"| {i} | {r['carrier']} | {r['name']} | {r['monthly']:,}원 | {r['total']:,}원 | {d} | {r['price_date']}" + (" ⚠ 오래됨" if r["stale"] else "") + " |")
    note = "\n\n⚠ 확인일이 30일 넘은 요금제는 현재 요금과 다를 수 있어요." if any(r["stale"] for r in ranked) else ""
    return "\n".join(lines) + note + "\n\n" + DISCLOSURE
