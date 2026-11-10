"""취향 맞춤 원두 구독: 추천, 로스팅 신선도, 배송 일정, 재고 확인 (결제·배송 연동 없음)."""
import datetime as dt

METHODS = {"에스프레소": "아주 곱게", "모카포트": "곱게", "핸드드립": "중간", "에어로프레스": "중간~중간 곱게", "프렌치프레스": "굵게", "콜드브루": "굵게"}
CYCLES = {"격주": 14, "매월": 28}
FRESH_MIN, FRESH_MAX, STALE = 5, 30, 45   # 로스팅 후 일수 기준(예시값)


def parse_date(s):
    return dt.date.fromisoformat(s)


def check_profile(p):
    err = []
    for k in ("acidity", "body", "bitter"):
        v = p.get(k)
        if not isinstance(v, int) or not 1 <= v <= 5: err.append(f"{k}는 1~5 정수여야 합니다")
    if p.get("method") not in METHODS: err.append("추출 방식은 " + "/".join(METHODS) + " 중 하나")
    if p.get("cycle") not in CYCLES: err.append("배송 주기는 " + "/".join(CYCLES) + " 중 하나")
    if not isinstance(p.get("grams", 0), int) or p.get("grams", 0) < 100: err.append("1회 용량은 100g 이상 정수")
    return err


def age(bean, today):
    return (today - parse_date(bean["roasted"])).days


def freshness(days):
    if days < 0: return "오류(로스팅일이 미래)"
    if days > STALE: return "제외(너무 오래됨)"
    if days < FRESH_MIN: return "가스 빼는 중(며칠 더 두면 좋음)"
    if days <= FRESH_MAX: return "마시기 좋음"
    return "신선도 떨어짐(주의)"


def distance(p, b):
    return abs(p["acidity"] - b["acidity"]) + abs(p["body"] - b["body"]) + abs(p["bitter"] - b["bitter"])


def recommend(p, beans, today, n=2):
    err = check_profile(p)
    if err: raise ValueError("; ".join(err))
    cand, skipped = [], []
    for b in beans:
        d = age(b, today)
        if p.get("decaf_only") and not b.get("decaf"): skipped.append((b["name"], "디카페 아님")); continue
        if not p.get("decaf_only") and b.get("decaf") and not p.get("allow_decaf", False): skipped.append((b["name"], "디카페(요청 시에만 추천)")); continue
        if d < 0 or d > STALE: skipped.append((b["name"], freshness(d))); continue
        if b["stock_g"] < p["grams"]: skipped.append((b["name"], f"재고 {b['stock_g']}g 부족")); continue
        if p["method"] not in b["methods"]: skipped.append((b["name"], f"{p['method']}에 맞지 않음")); continue
        cand.append((distance(p, b), d, b))
    cand.sort(key=lambda x: (x[0], x[1]))
    out = [{"name": b["name"], "score": 15 - dist, "match": dist, "days": d, "fresh": freshness(d), "price": b["price_per_200g"] * -(-p["grams"] // 200)} for dist, d, b in cand[:n]]
    return out, skipped


def schedule(p, start, count=4):
    start = parse_date(start) if isinstance(start, str) else start
    step = CYCLES[p["cycle"]]
    ds = []
    for i in range(count):
        d = start + dt.timedelta(days=step * i)
        while d.weekday() >= 5: d += dt.timedelta(days=1)    # 주말 배송 제외(예시)
        ds.append(d)
    return ds


def grind_note(method):
    return f"{method}: 분쇄도 {METHODS[method]}. 홀빈으로 받고 마시기 직전에 가는 쪽이 향이 오래 갑니다."


def plan(p, beans, today, start):
    recs, skipped = recommend(p, beans, today)
    return {"recs": recs, "skipped": skipped, "dates": schedule(p, start), "grind": grind_note(p["method"])}


def text(p, pl):
    L = []
    if not pl["recs"]: L.append("추천할 원두가 없습니다(재고·신선도 조건을 통과한 원두 없음).")
    for i, r in enumerate(pl["recs"], 1):
        L.append(f"{i}. {r['name']} - 취향 차이 {r['match']}점(낮을수록 비슷), 로스팅 후 {r['days']}일, {r['fresh']}, {r['price']:,}원")
    for n, w in pl["skipped"]: L.append(f"  (제외) {n}: {w}")
    L.append("배송 예정일: " + ", ".join(d.isoformat() for d in pl["dates"]))
    L.append(pl["grind"])
    L.append("※ 맛 취향 점수는 간단한 거리 계산이며 실제 맛 평가가 아닙니다. 결제·배송은 연동하지 않았습니다.")
    return "\n".join(L)
