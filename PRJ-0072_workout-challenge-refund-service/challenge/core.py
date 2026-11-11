"""운동 인증 기록을 검증하고 챌린지 환급액을 계산한다. 결제·송금은 하지 않으며 계산 결과 표만 만든다."""
import csv, datetime as dt, json
from collections import defaultdict

SPEED_MIN, SPEED_MAX = 3.0, 25.0        # 시속(km/h) 범위 밖이면 의심 기록(예시 기준)


def load_config(path):
    c = json.load(open(path, encoding="utf-8"))
    for k in ("start", "end", "goal_count", "min_distance_km", "min_minutes"):
        if k not in c: raise ValueError(f"설정에 '{k}'가 없습니다")
    c["start"], c["end"] = dt.date.fromisoformat(c["start"]), dt.date.fromisoformat(c["end"])
    if c["end"] < c["start"]: raise ValueError("종료일이 시작일보다 빠릅니다")
    if not isinstance(c["goal_count"], int) or c["goal_count"] < 1: raise ValueError("goal_count는 1 이상의 정수")
    c.setdefault("fee_rate", 0.1); c.setdefault("forfeit_use", "donate"); c.setdefault("partial_refund", False)
    if not 0 <= c["fee_rate"] <= 1: raise ValueError("fee_rate는 0~1")
    if c["forfeit_use"] not in ("donate", "bonus_pool"): raise ValueError("forfeit_use는 donate 또는 bonus_pool")
    return c


def read_participants(path):
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            u = (r.get("user") or "").strip()
            try: dep = int(r["deposit"])
            except (ValueError, KeyError, TypeError): raise ValueError(f"{i}행: 참가비(deposit)는 정수")
            if not u or u in out or dep <= 0: raise ValueError(f"{i}행: 사용자 id가 비었거나 중복이거나 참가비가 0 이하")
            out[u] = dep
    return out


def verify(logs_path, cfg, users, today):
    ok, bad = defaultdict(list), []
    proofs, perday = {}, set()
    with open(logs_path, encoding="utf-8-sig", newline="") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):
            u = (r.get("user") or "").strip()
            try: d = dt.date.fromisoformat(r["date"].strip()); km = float(r["distance_km"]); mn = float(r["minutes"]); pid = r["proof_id"].strip()
            except (ValueError, KeyError, AttributeError): bad.append((i, u, "형식 오류")); continue
            why = None
            if u not in users: why = "참가자가 아님"
            elif not cfg["start"] <= d <= cfg["end"]: why = "챌린지 기간 밖"
            elif d > today: why = "미래 날짜"
            elif km <= 0 or mn <= 0: why = "거리·시간이 0 이하"
            elif km < cfg["min_distance_km"] or mn < cfg["min_minutes"]: why = "최소 거리 또는 시간 미달"
            elif not pid: why = "인증 자료(proof_id) 없음"
            elif pid in proofs: why = f"인증 자료 중복({proofs[pid]}도 사용)"
            elif (u, d) in perday: why = "하루 1회만 인정"
            elif not SPEED_MIN <= km / (mn / 60) <= SPEED_MAX: why = f"속도 {km / (mn / 60):.1f}km/h가 이상함 - 직접 확인 필요"
            if why: bad.append((i, u, why)); continue
            proofs[pid] = u; perday.add((u, d)); ok[u].append(d)
    return ok, bad


def settle(cfg, deposits, ok):
    rows, forfeited = [], 0
    for u, dep in deposits.items():
        n = len(ok.get(u, [])); goal = cfg["goal_count"]
        if n >= goal: ref = dep
        elif cfg["partial_refund"]: ref = dep * n // goal
        else: ref = 0
        rows.append({"user": u, "deposit": dep, "verified": n, "goal": goal, "achieved": n >= goal, "refund": ref}); forfeited += dep - ref
    fee = int(forfeited * cfg["fee_rate"]); rest = forfeited - fee
    winners = [r for r in rows if r["achieved"]]
    bonus_total = 0
    if cfg["forfeit_use"] == "bonus_pool" and winners:
        share = rest // len(winners)
        for r in winners: r["bonus"] = share; bonus_total += share
    for r in rows: r.setdefault("bonus", 0)
    donate = rest - bonus_total
    return rows, {"deposits": sum(deposits.values()), "refunds": sum(r["refund"] for r in rows), "fee": fee, "bonus": bonus_total, "donate_or_remainder": donate}


def text(rows, tot, bad):
    L = [f"{r['user']}: 인증 {r['verified']}/{r['goal']}회 {'달성' if r['achieved'] else '미달'} → 환급 {r['refund']:,}원" + (f" + 보너스 {r['bonus']:,}원" if r["bonus"] else "") for r in rows]
    L.append(f"합계: 참가비 {tot['deposits']:,} = 환급 {tot['refunds']:,} + 수수료 {tot['fee']:,} + 보너스 {tot['bonus']:,} + 기부/잔액 {tot['donate_or_remainder']:,}")
    L += [f"인정 안 됨: {i}행 {u or '?'} - {w}" for i, u, w in bad]
    L.append("※ 계산 결과일 뿐 송금하지 않습니다. 기록은 사용자가 제출한 값이고 실제 운동 여부를 확인할 수 없습니다. 참가비를 걸고 보너스를 주는 방식은 사행성·금융 관련 법 검토가 필요하며 이 도구는 확인하지 않았습니다.")
    return "\n".join(L)
