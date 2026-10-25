"""취향·예산에 맞는 일정표 만들기(AI 없이 규칙 기반). 장소 목록은 사용자가 준 JSON만 쓴다."""
import math

PACE = {"relaxed": 3, "normal": 4, "packed": 5}
DAY_START, DAY_END = 9 * 60, 20 * 60
SPEED_KMH, BUFFER_MIN = 30, 10


class PlanError(ValueError):
    pass


def hm(t):
    h, m = t.split(":"); return int(h) * 60 + int(m)


def fmt(m):
    return f"{m // 60:02d}:{m % 60:02d}"


def km(a, b):
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"]); dl = math.radians(b["lon"] - a["lon"]); dp = p2 - p1
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def validate(places, days, budget, pace):
    if not places: raise PlanError("장소 목록이 비었습니다")
    if not isinstance(days, int) or not 1 <= days <= 14: raise PlanError("일수는 1~14")
    if budget < 0: raise PlanError("예산은 0 이상")
    if pace not in PACE: raise PlanError("속도는 relaxed/normal/packed")
    ids = set()
    for p in places:
        for k in ("id", "name", "category", "cost", "minutes", "open", "lat", "lon"):
            if k not in p: raise PlanError(f"장소 정보 부족({p.get('id', '?')}): {k}")
        if p["id"] in ids: raise PlanError(f"장소 id 중복: {p['id']}")
        ids.add(p["id"])
        if p["cost"] < 0 or p["minutes"] <= 0: raise PlanError(f"비용/시간 오류: {p['id']}")
        try:
            a, b = p["open"].split("-"); hm(a), hm(b)
        except Exception:
            raise PlanError(f"운영 시간 형식 오류(예 09:00-18:00): {p['id']}")


def plan(places, days, budget, interests=(), pace="normal"):
    validate(places, days, budget, pace)
    want = set(interests)
    ranked = sorted(places, key=lambda p: (-(2.0 if p["category"] in want else 0.5), p["cost"], p["id"]))
    chosen, spent = [], 0
    for p in ranked:
        if len(chosen) >= days * PACE[pace]: break
        if spent + p["cost"] <= budget: chosen.append(p); spent += p["cost"]
    if not chosen: return {"days": [], "spent": 0, "unscheduled": [], "skipped": [p["name"] for p in places]}
    tour, rest = [chosen[0]], chosen[1:]                           # 가까운 곳부터 이어 가는 순서
    while rest:
        nxt = min(rest, key=lambda p: (km(tour[-1], p), p["id"])); tour.append(nxt); rest.remove(nxt)
    per = PACE[pace]
    out, unsched = [], []
    for d in range(days):
        group, t, prev, items = tour[d * per:(d + 1) * per], DAY_START, None, []
        for p in group:
            move = 0 if prev is None else math.ceil(km(prev, p) / SPEED_KMH * 60) + BUFFER_MIN
            o, c = (hm(x) for x in p["open"].split("-"))
            start = max(t + move, o)
            if start + p["minutes"] > min(c, DAY_END): unsched.append(p); continue
            items.append({"place": p, "start": start, "end": start + p["minutes"], "move": move})
            t, prev = start + p["minutes"], p
        out.append(items)
    chosen_ids = {i["place"]["id"] for d in out for i in d}
    return {"days": out, "spent": sum(p["cost"] for p in chosen if p["id"] in chosen_ids), "unscheduled": [p["name"] for p in unsched],
            "skipped": [p["name"] for p in places if p not in chosen]}


def render(result, budget, currency="원"):
    o = ["# 여행 일정표", ""]
    links = False
    for i, day in enumerate(result["days"], 1):
        o.append(f"## {i}일차")
        if not day: o.append("- (일정 없음)")
        for it in day:
            p = it["place"]; line = f"- {fmt(it['start'])}~{fmt(it['end'])} **{p['name']}** ({p['category']}, {p['cost']:,}{currency})"
            if it["move"]: line += f" — 이동 약 {it['move']}분"
            if p.get("link"):
                line += f" [예약 링크]({p['link']})"; links = links or bool(p.get("affiliate"))
            o.append(line)
        o.append("")
    o.append(f"**사용 비용 {result['spent']:,}{currency} / 예산 {budget:,}{currency}**")
    if result["unscheduled"]: o.append("시간이 안 맞아 뺀 곳: " + ", ".join(result["unscheduled"]))
    if links: o.append("\n※ 일부 예약 링크는 제휴 링크이며, 이용 시 운영자가 수수료를 받을 수 있습니다.")
    o.append("\n※ 운영 시간·가격은 입력한 자료 기준입니다. 방문 전 공식 안내를 확인하세요. 이동 시간은 직선거리 기준 추정입니다.")
    return "\n".join(o) + "\n"
