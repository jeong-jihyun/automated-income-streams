"""중고 전자기기 매입가 산정·상태 등급·판매 글 초안. 시세 자료는 사용자가 CSV로 넣는다(크롤링 없음). 등급 계수·수리비는 예시값."""
import csv, statistics
from datetime import date, timedelta

GRADE_FACTOR = {"A": 1.00, "B": 0.90, "C": 0.78, "D": 0.60}
FUNCS = ["터치", "카메라", "스피커", "마이크", "와이파이", "블루투스", "충전"]
REPAIR_COST = {"터치": 60000, "카메라": 50000, "스피커": 25000, "마이크": 25000, "와이파이": 40000, "블루투스": 30000, "충전": 30000, "배터리": 45000}
MIN_SAMPLES, WINDOW_DAYS = 5, 60
BAD = ["새것 같은", "미개봉급", "완벽", "무조건", "하자 없음"]


class RefurbError(ValueError):
    pass


def load_comps(path):
    try: f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e: raise RefurbError(f"시세 파일을 열 수 없어요: {e}")
    rows = []
    with f:
        for i, r in enumerate(csv.DictReader(f), 2):
            try: rows.append({"model": r["model"].strip(), "price": int(r["price"]), "date": date.fromisoformat(r["date"]), "storage": r.get("storage", "").strip()})
            except (KeyError, ValueError): raise RefurbError(f"시세 파일 {i}행 형식 오류: {r}")
    return rows


def estimate(comps, model, today, storage=None):
    xs = [c["price"] for c in comps if c["model"] == model and (storage is None or c["storage"] == storage) and 0 <= (today - c["date"]).days <= WINDOW_DAYS]
    if len(xs) < MIN_SAMPLES: return {"ok": False, "n": len(xs), "reason": f"최근 {WINDOW_DAYS}일 거래가 {len(xs)}건뿐이라 시세를 정하기 어려워요(최소 {MIN_SAMPLES}건)"}
    xs.sort(); q1, q3 = statistics.quantiles(xs, n=4)[0], statistics.quantiles(xs, n=4)[2]; iqr = q3 - q1
    kept = [x for x in xs if q1 - 1.5 * iqr <= x <= q3 + 1.5 * iqr] or xs
    return {"ok": True, "n": len(xs), "used": len(kept), "median": round(statistics.median(kept)), "low": min(kept), "high": max(kept), "outliers": len(xs) - len(kept)}


def grade(check):
    """check: screen(0~3 흠집), body(0~3 찍힘), battery(%), broken(고장 기능 목록)"""
    for k in ("screen", "body", "battery"):
        if check.get(k) is None: raise RefurbError(f"점검 항목 '{k}'가 없어요")
    broken = check.get("broken", []); bad = [f for f in broken if f not in REPAIR_COST]
    if bad: raise RefurbError(f"알 수 없는 기능: {bad}")
    repair = sum(REPAIR_COST[f] for f in broken) + (REPAIR_COST["배터리"] if check["battery"] < 80 else 0)
    worst = max(check["screen"], check["body"])
    g = "D" if broken else "A" if worst == 0 and check["battery"] >= 85 else "B" if worst <= 1 and check["battery"] >= 80 else "C" if worst <= 2 else "D"
    return {"grade": g, "factor": GRADE_FACTOR[g], "repair": repair, "broken": broken}


def offer(est, gr, fee=0.04, target_profit=30000):
    if not est["ok"]: raise RefurbError(est["reason"])
    resale = round(est["median"] * gr["factor"]); net = resale * (1 - fee); price = int(max(0, (net - gr["repair"] - target_profit) // 1000 * 1000))
    return {"resale": resale, "buy_offer": price, "expected_profit": round(net - gr["repair"] - price), "note": "예상 판매가는 같은 모델의 최근 거래 중앙값 × 등급 계수예요. 실제로 팔리는 가격은 달라질 수 있어요"}


def listing(model, gr, check, gates):
    need = {"imei_checked": "분실·도난 기기 조회(IMEI 등)", "factory_reset_done": "개인정보 초기화·계정 로그아웃", "lost_stolen_clear": "분실·도난 아님 확인"}
    miss = [v for k, v in need.items() if not gates.get(k)]
    if miss: raise RefurbError("판매 글을 만들기 전에 확인이 필요해요: " + ", ".join(miss))
    parts = [f"# {model} 중고 (상태 {gr['grade']}등급)", "", f"- 배터리 성능: {check['battery']}%", f"- 화면 상태: {['흠집 없음', '미세 흠집', '눈에 띄는 흠집', '깊은 흠집'][check['screen']]}", f"- 외관: {['찍힘 없음', '미세 찍힘', '눈에 띄는 찍힘', '큰 찍힘'][check['body']]}"]
    parts.append("- 고장·수리 이력: " + (", ".join(gr["broken"]) + " 기능 이상(수리 전 상태)" if gr["broken"] else "점검한 기능은 모두 정상이에요"))
    parts += ["", "※ 점검한 항목 기준의 설명이며 사진과 함께 확인해 주세요. 개인정보는 초기화했어요."]
    t = "\n".join(parts)
    return t


def check_text(t):
    return [f"'{w}' 표현은 빼 주세요" for w in BAD if w in t]
