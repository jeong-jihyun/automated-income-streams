"""환율·금리 등 기준 가격 도달 알림 판정 (가격은 사용자가 준 CSV, 전송은 outbox 파일에만 기록)."""
import csv, datetime as dt, json, os, tempfile

OPS = {">=": lambda p, t: p >= t, "<=": lambda p, t: p <= t}
SPIKE = 0.20          # 직전 값 대비 20% 넘게 튀면 의심 값으로 보고 알리지 않음(예시)


def load_rules(path):
    rules = json.load(open(path, encoding="utf-8"))
    seen = set()
    for r in rules:
        for k in ("id", "pair", "op", "threshold"):
            if k not in r: raise ValueError(f"규칙에 '{k}'가 없습니다: {r}")
        if r["op"] not in OPS: raise ValueError(f"규칙 {r['id']}: op는 >= 또는 <=")
        if not isinstance(r["threshold"], (int, float)) or r["threshold"] <= 0: raise ValueError(f"규칙 {r['id']}: 기준값은 0보다 큰 숫자")
        if str(r["id"]).startswith("_"): raise ValueError(f"규칙 id는 _로 시작할 수 없습니다: {r['id']}")
        if r["id"] in seen: raise ValueError(f"규칙 id 중복: {r['id']}")
        seen.add(r["id"])
        r.setdefault("cooldown_min", 60); r.setdefault("rearm_pct", 0.2)
    return rules


def load_readings(path):
    rows, bad = [], 0
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            try:
                t = dt.datetime.fromisoformat(r["time"].strip()); p = float(r["price"])
                if p <= 0: raise ValueError
                rows.append((t, r["pair"].strip(), p))
            except (ValueError, KeyError, AttributeError):
                bad += 1
    rows.sort()
    return rows, bad


def load_state(path):
    if path and os.path.exists(path): return json.load(open(path, encoding="utf-8"))
    return {}


def save_state(path, st):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(st, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def evaluate(rules, readings, state=None, now=None, max_age_min=180):
    """조건을 '넘어서는 순간'에만 한 번 알림. 쿨다운 안에서는 알리지 않고, 기준에서 충분히 멀어지면 다시 장전."""
    st = {k: (dict(v) if k != "_seen" else dict(v)) for k, v in (state or {}).items()}
    seen = st.setdefault("_seen", {})            # 이미 처리한 시각 - 같은 가격 파일을 다시 돌려도 중복 알림 없음
    alerts, notes, prev = [], [], {}
    for t, pair, p in readings:
        if pair in seen and t.isoformat() <= seen[pair]: continue
        seen[pair] = t.isoformat()
        last = prev.get(pair)
        if last and abs(p - last) / last > SPIKE:
            notes.append(f"{t:%m-%d %H:%M} {pair} {p:g}: 직전 {last:g}에서 {SPIKE:.0%} 넘게 변해 의심 값으로 건너뜀"); continue
        prev[pair] = p
        for r in rules:
            if r["pair"] != pair: continue
            s = st.setdefault(r["id"], {"armed": True, "last_alert": None})
            hit = OPS[r["op"]](p, r["threshold"])
            if hit and s["armed"]:
                la = dt.datetime.fromisoformat(s["last_alert"]) if s["last_alert"] else None
                if la is None or (t - la).total_seconds() >= r["cooldown_min"] * 60:
                    s["armed"] = False; s["last_alert"] = t.isoformat()
                    alerts.append({"time": t.isoformat(), "rule": r["id"], "pair": pair, "price": p,
                                   "text": f"[기준가 도달] {pair} {p:,.2f} {r['op']} {r['threshold']:,.2f}"})
            elif not hit and not s["armed"]:
                m = r["threshold"] * r["rearm_pct"] / 100
                if (r["op"] == ">=" and p < r["threshold"] - m) or (r["op"] == "<=" and p > r["threshold"] + m): s["armed"] = True
    if now and readings:
        newest = max(t for t, _, _ in readings)
        if (now - newest).total_seconds() > max_age_min * 60: notes.append(f"가장 최근 가격이 {newest:%m-%d %H:%M}으로 오래됨 - 알림이 늦을 수 있음")
    return alerts, st, notes


def write_outbox(path, alerts):
    with open(path, "a", encoding="utf-8") as f:
        for a in alerts: f.write(json.dumps(a, ensure_ascii=False) + "\n")
