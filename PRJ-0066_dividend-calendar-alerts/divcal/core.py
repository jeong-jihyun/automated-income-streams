"""보유 종목 × 사용자가 넣은 배당 일정 → 예상 수령액, 임박 알림 글, 월별 표, .ics (수집·발송 없음)."""
import csv, datetime as dt

TAX_DEFAULT = 0.154      # 국내 배당소득세 예시값(실제 세금은 개인 상황에 따라 다름)


def _d(s, what):
    try: return dt.date.fromisoformat(s.strip())
    except ValueError: raise ValueError(f"{what} 날짜 형식 오류: '{s}' (YYYY-MM-DD)")


def read_holdings(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if rows and {"code", "name", "shares", "buy_date"} - set(rows[0]): raise ValueError("보유 파일에는 code,name,shares,buy_date 열이 필요합니다")
    out = {}
    for r in rows:
        try: sh = int(r["shares"])
        except ValueError: raise ValueError(f"{r['name']}: 수량이 정수가 아님")
        if sh <= 0: raise ValueError(f"{r['name']}: 수량은 1 이상")
        out[r["code"].strip()] = {"name": r["name"].strip(), "shares": sh, "buy": _d(r["buy_date"], r["name"])}
    return out


def read_schedule(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if rows and {"code", "ex_date", "pay_date", "per_share"} - set(rows[0]): raise ValueError("일정 파일에는 code,ex_date,pay_date,per_share 열이 필요합니다")
    out = []
    for r in rows:
        try: ps = float(r["per_share"].replace(",", ""))
        except ValueError: raise ValueError(f"{r['code']}: 주당 배당금이 숫자가 아님")
        ex, pay = _d(r["ex_date"], r["code"]), _d(r["pay_date"], r["code"])
        if pay < ex: raise ValueError(f"{r['code']}: 지급일이 배당락일보다 빠름")
        out.append({"code": r["code"].strip(), "ex": ex, "pay": pay, "ps": ps, "note": (r.get("note") or "").strip()})
    return out


def expected(holdings, schedule, tax=TAX_DEFAULT):
    """배당락일 전날까지 산 주식만 받는다고 가정(결제일 규칙은 시장마다 달라 사용자 입력 날짜를 그대로 사용)."""
    rows, unknown = [], []
    for s in schedule:
        h = holdings.get(s["code"])
        if not h: unknown.append(s["code"]); continue
        eligible = h["buy"] < s["ex"]
        gross = round(h["shares"] * s["ps"]) if eligible else 0
        rows.append({"code": s["code"], "name": h["name"], "shares": h["shares"], "ex": s["ex"], "pay": s["pay"], "ps": s["ps"],
                     "eligible": eligible, "gross": gross, "net": round(gross * (1 - tax)), "note": s["note"],
                     "why": "" if eligible else f"매수일 {h['buy']}이(가) 배당락일 {s['ex']}과 같거나 늦어 받지 못할 수 있음"})
    rows.sort(key=lambda r: (r["pay"], r["code"]))
    return rows, sorted(set(unknown))


def alerts(rows, today, days=7):
    out = []
    for r in rows:
        if not r["eligible"]: continue
        de, dp = (r["ex"] - today).days, (r["pay"] - today).days
        if 0 <= de <= days: out.append((r["ex"], f"[배당락 D-{de}] {r['name']} 배당락일 {r['ex']} ({'오늘' if de == 0 else str(de) + '일 뒤'}) - 이 날 이후 매수는 이번 배당 대상이 아닐 수 있음"))
        if 0 <= dp <= days: out.append((r["pay"], f"[지급 D-{dp}] {r['name']} 지급일 {r['pay']} 예상 {r['net']:,}원(세후 가정, 세전 {r['gross']:,}원)"))
    return [m for _, m in sorted(out)]


def monthly(rows):
    m = {}
    for r in rows:
        if r["eligible"]: k = r["pay"].strftime("%Y-%m"); m[k] = m.get(k, 0) + r["net"]
    return dict(sorted(m.items()))


def ics(rows):
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//divcal//KO"]
    for r in rows:
        if not r["eligible"]: continue
        for kind, d in (("배당락일", r["ex"]), ("배당 지급일", r["pay"])):
            L += ["BEGIN:VEVENT", f"UID:{r['code']}-{kind}-{d.isoformat()}@divcal", f"DTSTAMP:{d.strftime('%Y%m%d')}T000000Z",
                  f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}", f"SUMMARY:{r['name']} {kind}", "END:VEVENT"]
    L.append("END:VCALENDAR")
    return "\r\n".join(L) + "\r\n"


def text(rows, unknown, today, days=7):
    L = []
    for a in alerts(rows, today, days) or ["앞으로 %d일 안에 알릴 일정이 없습니다." % days]: L.append(a)
    L.append("-- 월별 예상 수령액(세후 가정) --")
    for k, v in monthly(rows).items(): L.append(f"{k}: {v:,}원")
    for r in rows:
        if not r["eligible"]: L.append(f"(제외) {r['name']}: {r['why']}")
    if unknown: L.append("보유 목록에 없는 종목 일정(무시): " + ", ".join(unknown))
    L.append("※ 배당 일정·금액은 사용자가 넣은 값 그대로이며 바뀔 수 있습니다. 세율은 예시 가정이고 투자 조언이 아닙니다. 알림은 글만 만들며 보내지 않습니다.")
    return "\n".join(L)
