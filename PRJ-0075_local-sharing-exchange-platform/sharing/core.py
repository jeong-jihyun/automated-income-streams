"""동네 나눔·교환 글 점검(금지 품목·위치 노출), 필요 글과 나눔 글 매칭, 만료 정리. 연락·거래 중개는 하지 않는다."""
import csv, math, datetime as dt

PROHIBITED = ["의약품", "처방약", "주류", "담배", "무기", "총", "칼날", "동물", "펫", "상품권", "현금"]
NEED = {"id", "kind", "title", "dong", "lat", "lon", "posted"}


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        miss = NEED - set(rd.fieldnames or [])
        if miss: raise ValueError(f"{path}: 필수 열이 없습니다 - " + ", ".join(sorted(miss)))
        out, seen = [], set()
        for i, r in enumerate(rd, start=2):
            r = {k: (v or "").strip() for k, v in r.items()}
            if r["kind"] not in ("offer", "want"): raise ValueError(f"{i}행: kind는 offer 또는 want")
            if not r["id"] or r["id"] in seen: raise ValueError(f"{i}행: id가 비었거나 중복")
            seen.add(r["id"])
            try: r["lat"], r["lon"] = float(r["lat"]), float(r["lon"]); r["posted"] = dt.date.fromisoformat(r["posted"])
            except ValueError: raise ValueError(f"{i}행: 좌표 또는 날짜 형식 오류")
            if not (-90 <= r["lat"] <= 90 and -180 <= r["lon"] <= 180): raise ValueError(f"{i}행: 좌표 범위 오류")
            out.append(r)
    return out


def check(p):
    """금지 품목·정확 위치 노출 점검. 문제 목록을 돌려준다."""
    why = [f"금지 품목 의심 '{w}'" for w in PROHIBITED if w in p["title"] + p.get("desc", "")]
    if not p["dong"]: why.append("동네(동) 정보 없음")
    return why


def public_location(p, nd=2):
    """공개용 위치: 동 이름과 반올림 좌표(소수 nd자리, 약 1km)만. 정확한 좌표는 내보내지 않는다."""
    return {"dong": p["dong"], "lat": round(p["lat"], nd), "lon": round(p["lon"], nd)}


def km(a, b):
    R = 6371.0; p1, p2 = math.radians(a["lat"]), math.radians(b["lat"]); dp = p2 - p1; dl = math.radians(b["lon"] - a["lon"])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def active(posts, today, days=14):
    return [p for p in posts if (today - p["posted"]).days <= days]


def expired(posts, today, days=14):
    return [p for p in posts if (today - p["posted"]).days > days]


def match(posts, today, max_km=2.0, days=14):
    ok, held = [], []
    for p in active(posts, today, days):
        (held if check(p) else ok).append(p)
    offers = [p for p in ok if p["kind"] == "offer"]; wants = [p for p in ok if p["kind"] == "want"]; res, used = [], set()
    for w in sorted(wants, key=lambda x: x["posted"]):
        cands = []
        for o in offers:
            if o["id"] in used: continue
            words = set(w["title"].split()) & set(o["title"].split())
            d = km(w, o)
            if words and d <= max_km: cands.append((-len(words), d, o["id"], o, sorted(words)))
        if cands:
            _, d, _, o, words = sorted(cands, key=lambda x: x[:3])[0]; used.add(o["id"])
            res.append({"want": w["id"], "offer": o["id"], "km": round(d, 2), "words": words})
    return res, held


def report(posts, today, max_km=2.0):
    res, held = match(posts, today, max_km); exp = expired(posts, today)
    L = [f"활성 글 {len(active(posts, today))}개, 만료 {len(exp)}개, 점검 보류 {len(held)}개, 매칭 후보 {len(res)}쌍"]
    for m in res: L.append(f"  매칭 후보: {m['want']} ↔ {m['offer']} ({m['km']}km, 겹친 말: {', '.join(m['words'])})")
    for p in held: L.append(f"  [보류] {p['id']}: " + "; ".join(check(p)))
    for p in exp: L.append(f"  [만료] {p['id']} ({p['posted']})")
    L.append("※ 매칭은 후보일 뿐이고 연락·거래는 하지 않습니다. 공개 위치는 동 이름과 약 1km 단위 좌표만 씁니다.")
    return "\n".join(L)
