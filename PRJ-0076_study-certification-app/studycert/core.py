"""공부 시간 기록 검증(겹침·하루 16시간 초과·미래 날짜), 연속 일수, 그룹 랭킹, 의심 패턴 표시. 사진·위치 확인은 하지 않는다."""
import csv, datetime as dt
from collections import defaultdict

NEED = {"member", "date", "start", "end"}
MAX_DAY_MIN = 16 * 60


def _t(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


def read(path, today):
    ok, bad = [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        miss = NEED - set(rd.fieldnames or [])
        if miss: raise ValueError(f"{path}: 필수 열이 없습니다 - " + ", ".join(sorted(miss)))
        for i, r in enumerate(rd, start=2):
            r = {k: (v or "").strip() for k, v in r.items()}
            try:
                d = dt.date.fromisoformat(r["date"]); s, e = _t(r["start"]), _t(r["end"])
            except (ValueError, AttributeError):
                bad.append((i, r.get("member", ""), "날짜/시간 형식 오류")); continue
            if not r["member"]: bad.append((i, "", "member가 비었음")); continue
            if d > today: bad.append((i, r["member"], "미래 날짜")); continue
            if e <= s: bad.append((i, r["member"], "끝나는 시간이 시작보다 빠르거나 같음")); continue
            ok.append({"row": i, "member": r["member"], "date": d, "start": s, "end": e, "min": e - s})
    return ok, bad


def validate(logs):
    """같은 사람의 겹치는 기록과 하루 16시간 초과를 걸러낸다. 겹치면 뒤 기록만 제외하고 이유를 남긴다."""
    by = defaultdict(list)
    for l in logs: by[(l["member"], l["date"])].append(l)
    good, rej = [], []
    for (m, d), ls in by.items():
        ls.sort(key=lambda x: (x["start"], x["row"])); kept, tot = [], 0
        for l in ls:
            if kept and l["start"] < kept[-1]["end"]: rej.append((l["row"], m, "시간이 겹침")); continue
            if tot + l["min"] > MAX_DAY_MIN: rej.append((l["row"], m, "하루 16시간 초과")); continue
            kept.append(l); tot += l["min"]
        good += kept
    return good, sorted(rej)


def streak(days, today):
    """오늘(또는 어제)까지 이어진 연속 일수. 오늘 기록이 없어도 어제까지 이어졌으면 유지."""
    ds = set(days); cur = today if today in ds else today - dt.timedelta(days=1); n = 0
    while cur in ds: n += 1; cur -= dt.timedelta(days=1)
    return n


def ranking(logs, since, until):
    tot, days = defaultdict(int), defaultdict(set)
    for l in logs:
        if since <= l["date"] <= until: tot[l["member"]] += l["min"]; days[l["member"]].add(l["date"])
    rows = [{"member": m, "min": t, "days": len(days[m])} for m, t in tot.items()]
    rows.sort(key=lambda r: (-r["min"], -r["days"], r["member"]))
    rank, prev = 0, None
    for i, r in enumerate(rows, start=1):
        key = (r["min"], r["days"])
        if key != prev: rank = i
        r["rank"] = rank; prev = key
    return rows


def flags(logs, repeat=4):
    """같은 길이(분)가 repeat번 이상 반복되는 사람을 표시. 부정 확정이 아니라 확인 대상 표시일 뿐이다."""
    c = defaultdict(lambda: defaultdict(int))
    for l in logs: c[l["member"]][l["min"]] += 1
    return sorted((m, mn, n) for m, d in c.items() for mn, n in d.items() if n >= repeat)


def hm(m): return f"{m // 60}시간 {m % 60}분"


def report(logs, bad, rej, today, since, until):
    rk = ranking(logs, since, until)
    L = [f"기간 {since}~{until}: 유효 기록 {len(logs)}건, 제외 {len(bad) + len(rej)}건"]
    for r in rk:
        st = streak([l["date"] for l in logs if l["member"] == r["member"]], today)
        L.append(f"  {r['rank']}위 {r['member']}: {hm(r['min'])} ({r['days']}일, 연속 {st}일)")
    for row, m, why in bad + rej: L.append(f"  [제외] {row}행 {m}: {why}")
    for m, mn, n in flags(logs): L.append(f"  [확인] {m}: {mn}분 기록이 {n}번 반복됨 (부정 확정 아님)")
    L.append("※ 기록은 스스로 입력한 값이라 사진·위치 등 실제 공부 여부는 확인하지 않습니다.")
    return "\n".join(L)
