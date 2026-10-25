"""칼로리 '범위' 추정. 단정하지 않고, 확신이 낮거나 목록에 없는 음식은 사용자 확인을 요청한다."""
from . import nutrition as N

LOW_CONF = 0.6
DISCLAIMER = "※ 사진과 평균값으로 짐작한 대략치입니다(오차가 클 수 있어요). 의학적 판단이나 식단 지시가 아닙니다."


def one(label, portion, conf=1.0):
    if label not in N.FOODS: return {"label": label, "known": False}
    kcal, carb, prot, fat, serving = N.FOODS[label]
    if isinstance(portion, str) and portion.endswith("g"):
        try: grams = float(portion[:-1])
        except ValueError: raise N.FoodError(f"양 형식 오류: {portion}")
    elif portion in N.PORTION: grams = serving * N.PORTION[portion]
    else: raise N.FoodError(f"양은 S/M/L 또는 120g 형식: {portion}")
    if not 5 <= grams <= 3000: raise N.FoodError(f"양이 비정상입니다(5~3000g): {grams:g}g")
    unc = N.UNCERTAINTY + (0.15 if conf < LOW_CONF else 0)
    f = grams / 100
    mid = kcal * f
    return {"label": label, "known": True, "grams": round(grams), "kcal": round(mid), "low": round(mid * (1 - unc)), "high": round(mid * (1 + unc)),
            "carb": round(carb * f, 1), "protein": round(prot * f, 1), "fat": round(fat * f, 1), "confirm": conf < LOW_CONF}


def estimate(items):
    """items: [(라벨, 양, 확신도)]. 합계 범위, 확인 필요 항목, 목록에 없는 항목을 돌려준다."""
    rows = [one(*it) for it in items]
    known = [r for r in rows if r["known"]]
    return {"rows": known, "unknown": [r["label"] for r in rows if not r["known"]], "confirm": [r["label"] for r in known if r["confirm"]],
            "kcal": sum(r["kcal"] for r in known), "low": sum(r["low"] for r in known), "high": sum(r["high"] for r in known),
            "carb": round(sum(r["carb"] for r in known), 1), "protein": round(sum(r["protein"] for r in known), 1), "fat": round(sum(r["fat"] for r in known), 1)}


def text(res):
    if not res["rows"] and not res["unknown"]: return "음식이 인식되지 않았어요. 직접 입력해 주세요.\n" + DISCLAIMER
    o = [f"- {r['label']} 약 {r['grams']}g: 대략 {r['kcal']}kcal ({r['low']}~{r['high']})" + (" ← 맞는지 확인해 주세요" if r["confirm"] else "") for r in res["rows"]]
    if res["rows"]: o.append(f"합계 대략 {res['kcal']}kcal (범위 {res['low']}~{res['high']}), 탄수화물 {res['carb']}g · 단백질 {res['protein']}g · 지방 {res['fat']}g")
    if res["unknown"]: o.append("목록에 없어 계산에서 뺀 음식: " + ", ".join(res["unknown"]))
    return "\n".join(o) + "\n" + DISCLAIMER
