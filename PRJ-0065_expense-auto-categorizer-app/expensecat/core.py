"""카드 문자(붙여넣은 글)를 읽어 지출을 분류하고 월간 리포트를 만든다. 문자함 접근·은행 연결 없음."""
import csv, datetime as dt, json, os, re, tempfile
from collections import defaultdict

AMT = re.compile(r"([\d,]+)\s*원")
DATE = re.compile(r"(?<!\d)(\d{1,2})/(\d{1,2})(?!\d)")
TIME = re.compile(r"(?<!\d)(\d{1,2}):(\d{2})(?!\d)")
CUT = re.compile(r"\s*(누적|잔액|한도|총|\(일시불\)|일시불|\d개월).*$")


def split_messages(text):
    parts = re.split(r"(?:\[Web발신\]|\n\s*\n|-{3,})", text)
    return [p.strip() for p in parts if p.strip()]


def parse_one(msg, year):
    m = AMT.search(msg)
    d = DATE.search(msg)
    if not (m and d): return None
    kind = "취소" if "취소" in msg else ("승인" if "승인" in msg or "결제" in msg else None)
    if not kind: return None
    amount = int(m.group(1).replace(",", ""))
    mo, da = int(d.group(1)), int(d.group(2))
    try:
        date = dt.date(year, mo, da)
    except ValueError:
        return None
    t = TIME.search(msg, d.end())
    tail = msg[(t.end() if t else d.end()):]
    merchant = CUT.sub("", tail.replace("\n", " ")).strip(" -:,")
    if not merchant:        # 가맹점이 날짜 앞에 오는 형식
        head = msg[:m.start()].replace("\n", " ")
        merchant = re.sub(r"\[[^\]]*\]|\d{4}|승인|취소|결제|[가-힣]\*[가-힣]|님", " ", head)
        merchant = re.sub(r"\s+", " ", merchant).strip()
    merchant = re.sub(r"\s+", " ", merchant)
    return {"date": date, "time": t.group(0) if t else "", "kind": kind, "amount": amount, "merchant": merchant or "(가맹점 불명)"}


def parse(text, today=None):
    today = today or dt.date.today()
    out, bad = [], []
    for msg in split_messages(text):
        yr = today.year
        r = parse_one(msg, yr)
        if r and r["date"] > today + dt.timedelta(days=1):
            r = parse_one(msg, yr - 1)
        if r: out.append(r)
        else: bad.append(msg.replace("\n", " ")[:40])
    return out, bad


def categorize(merchant, user_rules, rules):
    low = merchant.lower()
    for src in (user_rules or {}, rules):
        for cat, kws in src.items():
            if any(k.lower() in low for k in kws): return cat
    return "미분류"


def settle(txs):
    """중복 문자 제거 + 취소 문자와 짝이 맞는 승인 제거."""
    seen, uniq, dup = set(), [], 0
    for t in txs:
        k = (t["date"], t["time"], t["kind"], t["amount"], t["merchant"])
        if k in seen: dup += 1; continue
        seen.add(k); uniq.append(t)
    appr = [t for t in uniq if t["kind"] == "승인"]
    cancelled, unmatched = [], []
    for c in [t for t in uniq if t["kind"] == "취소"]:
        hit = next((a for a in appr if a["amount"] == c["amount"] and a["merchant"] == c["merchant"] and a["date"] <= c["date"]), None)
        if hit: appr.remove(hit); cancelled.append(hit)
        else: unmatched.append(c)
    return appr, cancelled, unmatched, dup


def report(txs, rules, user_rules=None, month=None):
    appr, cancelled, unmatched, dup = settle(txs)
    if month: appr = [t for t in appr if t["date"].strftime("%Y-%m") == month]
    cat, merch = defaultdict(int), defaultdict(int)
    rows = []
    for t in appr:
        c = categorize(t["merchant"], user_rules, rules)
        cat[c] += t["amount"]; merch[t["merchant"]] += t["amount"]
        rows.append(dict(t, category=c))
    total = sum(cat.values())
    return {"rows": rows, "total": total, "by_cat": dict(sorted(cat.items(), key=lambda x: -x[1])),
            "top": sorted(merch.items(), key=lambda x: -x[1])[:5], "cancelled": cancelled, "unmatched_cancel": unmatched,
            "dup": dup, "uncat": sorted({r["merchant"] for r in rows if r["category"] == "미분류"})}


def to_text(rep, month=None):
    L = [f"## {month or '전체'} 지출 리포트", f"총 지출 {rep['total']:,}원 (취소 {len(rep['cancelled'])}건 반영)"]
    for c, v in rep["by_cat"].items():
        L.append(f"- {c}: {v:,}원 ({v / rep['total'] * 100:.0f}%)" if rep["total"] else f"- {c}: {v:,}원")
    L.append("자주 쓴 곳: " + ", ".join(f"{m} {v:,}원" for m, v in rep["top"]))
    if rep["dup"]: L.append(f"같은 문자가 두 번 들어와 {rep['dup']}건을 뺐습니다.")
    if rep["unmatched_cancel"]: L.append(f"짝이 되는 승인 문자를 못 찾은 취소 {len(rep['unmatched_cancel'])}건(이전 달 결제일 수 있음)")
    if rep["uncat"]: L.append("미분류 가맹점(규칙 추가 필요): " + ", ".join(rep["uncat"]))
    L.append("※ 분류는 키워드 규칙이라 틀릴 수 있습니다. 문자함·은행에는 접근하지 않고, 붙여넣은 글만 읽습니다.")
    return "\n".join(L)


def _safe(v):
    v = str(v)
    return "'" + v if v and v[0] in "=+-@" else v


def export(rep, path):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f); w.writerow(["날짜", "시간", "가맹점", "금액", "분류"])
        for r in rep["rows"]:
            w.writerow([r["date"].isoformat(), r["time"], _safe(r["merchant"]), r["amount"], r["category"]])


def learn(path, merchant, category):
    """사용자가 고친 분류를 규칙 파일에 저장(임시파일 후 교체)."""
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    kws = data.setdefault(category, [])
    if merchant not in kws: kws.append(merchant)
    for c, k in data.items():
        if c != category and merchant in k: k.remove(merchant)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)))
    with os.fdopen(fd, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
