"""광고 관리자에서 내려받은 CSV(메타·네이버)를 합쳐 주간 성과 보고서를 만든다. API 연결 없음 — 사용자가 내려받은 파일만 읽는다.
열 이름 매핑은 **예시**이며 실제 내려받기 파일의 열 이름과 다를 수 있다(다르면 --map 으로 지정)."""
import csv, json
from datetime import date, timedelta

MAPS = {
    "meta": {"date": "Day", "campaign": "Campaign name", "spend": "Amount spent (KRW)", "impressions": "Impressions", "clicks": "Link clicks", "conversions": "Results", "value": "Purchase conversion value"},
    "naver": {"date": "일별", "campaign": "캠페인", "spend": "총비용(VAT포함 원)", "impressions": "노출수", "clicks": "클릭수", "conversions": "전환수", "value": "전환매출액(원)"},
}
REQUIRED = ("date", "spend", "impressions", "clicks", "conversions")


class ReportError(ValueError):
    pass


def num(s, where):
    s = (s or "").replace(",", "").strip()
    if s in ("", "-"): return 0.0
    try: v = float(s)
    except ValueError: raise ReportError(f"{where}: 숫자가 아니에요 ('{s}')")
    if v < 0: raise ReportError(f"{where}: 음수예요 ({s})")
    return v


def load_csv(path, platform, mapping=None):
    m = dict(MAPS.get(platform, {})); m.update(mapping or {})
    try: f = open(path, encoding="utf-8-sig", newline="")
    except OSError as e: raise ReportError(f"파일을 열 수 없어요: {e}")
    with f:
        r = csv.DictReader(f); cols = r.fieldnames or []
        miss = [m[k] for k in REQUIRED if m.get(k) not in cols]
        if miss: raise ReportError(f"{platform}: 필요한 열이 없어요 {miss} (있는 열: {cols}). --map 으로 열 이름을 알려 주세요")
        rows = []
        for i, row in enumerate(r, 2):
            try: d = date.fromisoformat(row[m["date"]].strip().replace(".", "-").replace("/", "-").rstrip("-"))
            except ValueError: raise ReportError(f"{path} {i}행: 날짜 형식 오류 ('{row[m['date']]}')")
            w = f"{path} {i}행"
            rows.append({"platform": platform, "date": d, "campaign": row.get(m.get("campaign", ""), "") or "-", "spend": num(row[m["spend"]], w), "impressions": num(row[m["impressions"]], w),
                         "clicks": num(row[m["clicks"]], w), "conversions": num(row[m["conversions"]], w), "value": num(row.get(m.get("value", ""), ""), w) if m.get("value") in cols else None})
    return rows


def monday(d):
    return d - timedelta(days=d.weekday())


def agg(rows, week, platform=None):
    sel = [r for r in rows if monday(r["date"]) == week and (platform is None or r["platform"] == platform)]
    t = {k: sum(r[k] for r in sel) for k in ("spend", "impressions", "clicks", "conversions")}
    vals = [r["value"] for r in sel]; t["value"] = sum(v for v in vals if v is not None) if sel and all(v is not None for v in vals) else None
    t["days"] = len({r["date"] for r in sel}); return t


def metrics(t):
    div = lambda a, b: a / b if b else None
    return {**t, "ctr": div(t["clicks"], t["impressions"]), "cpc": div(t["spend"], t["clicks"]), "cpa": div(t["spend"], t["conversions"]), "roas": div(t["value"], t["spend"]) if t["value"] is not None else None}


def change(cur, prev):
    return None if cur is None or not prev else (cur - prev) / prev * 100


def flags(m, prev=None):
    out = []
    if m["days"] < 7: out.append(f"데이터가 {m['days']}일치만 있어요(주간 합계가 작게 보일 수 있어요)")
    if m["spend"] > 0 and m["conversions"] == 0: out.append("비용은 썼지만 전환이 0이에요")
    if 0 < m["clicks"] < 30: out.append("클릭이 30 미만이라 비율(전환 등)은 우연일 수 있어요")
    if prev and change(m["cpa"], prev["cpa"]) is not None and change(m["cpa"], prev["cpa"]) >= 30: out.append("전환당 비용(CPA)이 지난주보다 30% 이상 올랐어요")
    return out


def fmt(v, kind):
    if v is None: return "-"
    return {"won": f"{v:,.0f}원", "n": f"{v:,.0f}", "pct": f"{v * 100:.2f}%", "x": f"{v:.2f}배"}[kind]


def report(rows, week):
    prev_w = week - timedelta(days=7); plats = sorted({r["platform"] for r in rows}) or []
    if not rows: raise ReportError("데이터가 없어요")
    out = [f"# 주간 광고 성과 ({week} ~ {week + timedelta(days=6)})", ""]
    for p in [None] + plats:
        cur, prv = metrics(agg(rows, week, p)), metrics(agg(rows, prev_w, p))
        out += [f"## {'전체' if p is None else p}", "", "| 지표 | 이번 주 | 지난주 | 변화 |", "|---|---|---|---|"]
        for lab, k, kind in [("비용", "spend", "won"), ("노출", "impressions", "n"), ("클릭", "clicks", "n"), ("전환", "conversions", "n"), ("클릭률(CTR)", "ctr", "pct"), ("클릭당 비용(CPC)", "cpc", "won"), ("전환당 비용(CPA)", "cpa", "won"), ("광고수익률(ROAS)", "roas", "x")]:
            c = change(cur[k], prv[k]); out.append(f"| {lab} | {fmt(cur[k], kind)} | {fmt(prv[k], kind)} | {'-' if c is None else f'{c:+.1f}%'} |")
        fl = flags(cur, prv if prv["days"] else None); out += [""] + ([f"- ⚠ {x}" for x in fl] or ["- 특이사항 없음"]) + [""]
    out.append("※ 합계는 내려받은 파일 기준이며 광고 관리자 화면과 시간대·attribution(전환 귀속) 기준이 달라 차이가 날 수 있습니다.")
    return "\n".join(out) + "\n"
