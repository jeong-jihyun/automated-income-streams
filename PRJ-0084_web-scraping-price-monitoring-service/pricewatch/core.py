"""가격 기록 CSV로 하락·목표가·최저가 알림을 만든다. 웹에서 가격을 가져오지(수집) 않는다. 기록은 사람이 넣는다."""
import csv, datetime as dt, json, statistics

DROP = 0.10      # 직전 기록보다 10% 이상 내리면 알림(예시 설정)
STALE_DAYS = 7   # 마지막 기록이 이보다 오래되면 경고
COLS = ["date", "item", "price"]


def read(path):
    d, bad = {}, []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        miss = [c for c in COLS if c not in (rd.fieldnames or [])]
        if miss:
            raise ValueError("열이 없습니다: " + ", ".join(miss))
        for n, r in enumerate(rd, start=2):
            try:
                day = dt.date.fromisoformat(r["date"].strip()); p = int(r["price"].replace(",", "").strip())
                it = r["item"].strip()
                if p <= 0 or not it:
                    raise ValueError
                d.setdefault(it, {})[day] = p   # 같은 날 중복은 마지막 값
            except (ValueError, AttributeError):
                bad.append((n, "날짜·상품·가격 형식 오류"))
    return {k: sorted(v.items()) for k, v in d.items()}, bad


def load_targets(path):
    t = json.load(open(path, encoding="utf-8"))
    if not isinstance(t, dict) or not all(isinstance(v, int) and v > 0 for v in t.values()):
        raise ValueError("목표가 파일은 {상품: 가격(정수)} 형식이어야 합니다")
    return t


def analyze(hist, targets=None, today=None):
    targets = targets or {}; out = []
    for item, recs in sorted(hist.items()):
        prices = [p for _, p in recs]; last_day, last = recs[-1]
        med = statistics.median(prices); notes = []
        if len(prices) >= 3 and (last < med * 0.5 or last > med * 2):
            notes.append("입력 오류 의심(중앙값과 너무 다름): 알림 보류")
            out.append({"item": item, "last": last, "min": min(prices), "notes": notes, "alert": False}); continue
        prev = prices[-2] if len(prices) > 1 else None
        if prev and last <= prev * (1 - DROP):
            notes.append(f"직전 대비 {round((last - prev) / prev * 100, 1)}% 하락")
        if len(prices) >= 3 and last == min(prices) and last < prev:
            notes.append("기록상 최저가")
        if item in targets and last <= targets[item]:
            notes.append(f"목표가 {targets[item]:,}원 이하")
        if today and (today - last_day).days > STALE_DAYS:
            notes.append(f"기록이 {(today - last_day).days}일 전이라 오래됨")
        out.append({"item": item, "last": last, "min": min(prices), "notes": notes,
                    "alert": any("하락" in x or "최저가" in x or "목표가" in x for x in notes)})
    return out


def report(res, bad):
    lines = []
    for r in res:
        lines.append(f"{'★ ' if r['alert'] else '  '}{r['item']}: 현재 {r['last']:,}원 (최저 {r['min']:,}원)" + ("" if not r["notes"] else " — " + "; ".join(r["notes"])))
    lines += [f"[제외] {n}행: {w}" for n, w in bad]
    lines.append("※ 가격은 직접 넣은 기록입니다. 이 도구는 쇼핑몰에서 가격을 가져오지 않으며, 실제 현재가와 다를 수 있습니다.")
    return "\n".join(lines)
