"""견적서·청구서 만들기: 공급가액·부가세·합계 계산, 번호 매기기, HTML 출력. 전자세금계산서 발행은 하지 않는다."""
import datetime as dt, html, json, re
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP, InvalidOperation

VAT_RATE = Decimal("0.1")  # 예시 설정값(세율은 바뀔 수 있음)
PREFIX = {"quote": "Q", "invoice": "I"}
TITLE = {"quote": "견적서", "invoice": "청구서"}
DIGIT = "영일이삼사오육칠팔구"


def biz_no_ok(s):
    """사업자등록번호 형식(000-00-00000)과 검증 숫자 확인. 실제 등록 여부는 확인하지 못한다."""
    m = re.fullmatch(r"(\d{3})-(\d{2})-(\d{5})", s or "")
    if not m:
        return False
    d = [int(c) for c in "".join(m.groups())]
    w = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    t = sum(a * b for a, b in zip(d[:9], w)) + (d[8] * 5) // 10
    return (10 - t % 10) % 10 == d[9]


def money(x, rounding="floor"):
    return int(Decimal(x).to_integral_value(ROUND_FLOOR if rounding == "floor" else ROUND_HALF_UP))


def load(path):
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return validate(d)


def validate(d):
    errs = []
    if d.get("type") not in PREFIX:
        errs.append("type은 quote 또는 invoice")
    try:
        dt.date.fromisoformat(d.get("date", ""))
    except ValueError:
        errs.append("date 형식 오류(YYYY-MM-DD)")
    if not (d.get("client") or {}).get("name"):
        errs.append("받는 곳 이름이 없음")
    if not (d.get("supplier") or {}).get("name"):
        errs.append("공급자 이름이 없음")
    for who in ("supplier", "client"):
        b = (d.get(who) or {}).get("biz_no")
        if b and not biz_no_ok(b):
            errs.append(f"{who} 사업자번호 형식·검증 숫자 오류")
    items = d.get("items") or []
    if not items:
        errs.append("품목이 없음")
    for i, it in enumerate(items, 1):
        try:
            if Decimal(str(it["qty"])) <= 0 or Decimal(str(it["unit_price"])) < 0:
                errs.append(f"품목 {i}: 수량은 0보다 크고 단가는 0 이상")
        except (KeyError, InvalidOperation):
            errs.append(f"품목 {i}: qty/unit_price 숫자 필요")
    try:
        p = Decimal(str(d.get("discount_pct", 0)))
        if not 0 <= p <= 100:
            errs.append("discount_pct는 0~100")
    except InvalidOperation:
        errs.append("discount_pct 숫자 필요")
    if d.get("rounding", "floor") not in ("floor", "half_up"):
        errs.append("rounding은 floor 또는 half_up")
    if errs:
        raise ValueError("; ".join(errs))
    return d


def calc(d):
    r = d.get("rounding", "floor")
    lines = []
    for it in d["items"]:
        lines.append({"name": it["name"], "qty": Decimal(str(it["qty"])), "unit": Decimal(str(it["unit_price"])),
                      "amount": money(Decimal(str(it["qty"])) * Decimal(str(it["unit_price"])), r)})
    sub = sum(l["amount"] for l in lines)
    disc = money(Decimal(sub) * Decimal(str(d.get("discount_pct", 0))) / 100, r)
    supply = sub - disc
    vat = money(Decimal(supply) * VAT_RATE, r) if d.get("vat", True) else 0
    return {"lines": lines, "sub": sub, "discount": disc, "supply": supply, "vat": vat, "total": supply + vat}


def korean_amount(n):
    if n == 0:
        return "영"
    out = ""
    for unit, name in ((10 ** 12, "조"), (10 ** 8, "억"), (10 ** 4, "만"), (1, "")):
        part, n = divmod(n, unit)
        if part:
            s = ""
            for v, u in ((1000, "천"), (100, "백"), (10, "십"), (1, "")):
                dgt, part = divmod(part, v)
                if dgt:
                    s += (DIGIT[dgt] if not (dgt == 1 and u) else "") + u
            out += s + name
    return out


def next_number(kind, date, existing):
    """같은 종류·같은 달 번호의 다음 값. 형식: Q-202611-001."""
    head = f"{PREFIX[kind]}-{date[:4]}{date[5:7]}-"
    nums = [int(x[len(head):]) for x in existing if x.startswith(head) and x[len(head):].isdigit()]
    return head + f"{max(nums, default=0) + 1:03d}"


def render(d, number, c):
    e = html.escape
    rows = "".join(f"<tr><td>{e(l['name'])}</td><td>{l['qty'].normalize():f}</td><td>{int(l['unit']):,}</td><td>{l['amount']:,}</td></tr>" for l in c["lines"])
    note = "" if d.get("vat", True) else "<p>부가세 별도 표기 없음(면세·간이 등은 직접 확인)</p>"
    return f"""<!doctype html><html lang="ko"><meta charset="utf-8"><title>{TITLE[d['type']]} {e(number)}</title>
<h1>{TITLE[d['type']]}</h1><p>번호 {e(number)} · 날짜 {e(d['date'])}</p>
<p>공급자: {e(d['supplier']['name'])} {e(d['supplier'].get('biz_no', ''))}<br>받는 곳: {e(d['client']['name'])} 귀하</p>
<table border="1" cellpadding="4"><tr><th>품목</th><th>수량</th><th>단가</th><th>금액</th></tr>{rows}</table>
<p>소계 {c['sub']:,}원 · 할인 {c['discount']:,}원 · 공급가액 {c['supply']:,}원 · 부가세 {c['vat']:,}원</p>
<h2>합계 {c['total']:,}원 (일금 {korean_amount(c['total'])}원정)</h2>{note}
<p><small>이 문서는 세금계산서가 아니며 전자세금계산서 발행은 하지 않습니다.</small></p></html>
"""
