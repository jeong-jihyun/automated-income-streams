"""글자 → 표 항목. 영수증(상호·날짜·품목·합계·부가세)과 명함(이름·회사·전화·이메일·주소). 사람이 확인할 수 있도록 못 찾은 항목은 None으로 둔다."""
import re

DATE = re.compile(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?")
MONEY = r"(\d{1,3}(?:,\d{3})+|\d+)"
BIZ = re.compile(r"\b(\d{3}-\d{2}-\d{5})\b")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"(?<!\d)(0\d{1,2}-\d{3,4}-\d{4})(?!\d)")


def to_int(s):
    return int(s.replace(",", ""))


def parse_receipt(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    out = {"store": lines[0] if lines else None, "date": None, "biz_no": None, "items": [], "total": None, "vat": None, "warnings": []}
    for l in lines:
        m = DATE.search(l)
        if m and not out["date"]:
            y, mo, d, hh, mm = m.groups()
            out["date"] = f"{y}-{int(mo):02d}-{int(d):02d}" + (f" {int(hh):02d}:{mm}" if hh else "")
        b = BIZ.search(l)
        if b: out["biz_no"] = b.group(1)
        m = re.match(rf"^(합계|총\s*금액|총액|TOTAL)\D*{MONEY}\s*원?$", l, re.I)
        if m: out["total"] = to_int(m.group(2)); continue
        m = re.match(rf"^(부가세|VAT)\D*{MONEY}\s*원?$", l, re.I)
        if m: out["vat"] = to_int(m.group(2)); continue
        m = re.match(rf"^(?P<n>[^\d].*?)\s+(?P<q>\d{{1,3}})\s+{MONEY}$", l)      # 품목명 수량 금액
        if m and not re.search(r"결제|카드|승인|사업자", l):
            out["items"].append({"name": m.group("n"), "qty": int(m.group("q")), "amount": to_int(m.group(3))})
    if out["total"] is None: out["warnings"].append("합계를 찾지 못했습니다")
    if not out["date"]: out["warnings"].append("날짜를 찾지 못했습니다")
    if out["items"] and out["total"] is not None:
        s = sum(i["amount"] for i in out["items"])
        if s != out["total"]:
            out["warnings"].append(f"품목 합({s:,})과 합계({out['total']:,})가 다릅니다 — 인식 오류를 확인하세요")
    return out


def parse_namecard(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    email = EMAIL.search(text)
    phones = PHONE.findall(text)
    mobile = next((p for p in phones if p.startswith("01")), None)
    tel = next((p for p in phones if not p.startswith("01")), None)
    company = next((l for l in lines if re.search(r"\(주\)|주식회사|㈜|Co\.|Inc|Corp", l)), None)
    address = next((l for l in lines if re.search(r"(특별시|광역시|도)\s|[시군구]\s.*[로길]\s?\d", l)), None)
    name = None
    for l in lines:
        if l == company or l == address or EMAIL.search(l) or PHONE.search(l):
            continue
        m = re.match(r"^([가-힣]{2,4})(?:\s+\S+)?$", l)
        if m:
            name = m.group(1); break
    out = {"name": name, "company": company, "mobile": mobile, "tel": tel, "email": email.group(0) if email else None, "address": address, "warnings": []}
    for k in ("name", "mobile", "email"):
        if not out[k]: out["warnings"].append(f"{k}을(를) 찾지 못했습니다")
    return out
