"""개인정보 찾기(정규식 + 검증). 찾은 구간 목록을 돌려준다. 이름은 '이름:' 같은 라벨이 붙은 경우만 찾는다(오탐 방지)."""
import ipaddress
import re
from datetime import date

PATTERNS = [
    ("rrn", re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{2})-?([1-8])(\d{6})(?!\d)")),
    ("card", re.compile(r"(?<!\d)(?:\d{4}[- ]?){3}\d{4}(?!\d)")),
    ("biz", re.compile(r"(?<!\d)\d{3}-\d{2}-\d{5}(?!\d)")),
    ("mobile", re.compile(r"(?<!\d)01[016789][-. ]?\d{3,4}[-. ]?\d{4}(?!\d)")),
    ("phone", re.compile(r"(?<!\d)0(?:2|[3-6]\d)[-. ]?\d{3,4}[-. ]?\d{4}(?!\d)")),
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("ip", re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")),
    ("address", re.compile(r"(?:서울특별시|서울시|부산광역시|대구광역시|인천광역시|광주광역시|대전광역시|울산광역시|세종특별자치시|경기도|강원도|충청[남북]도|전라[남북]도|경상[남북]도|제주특별자치도)\s*[가-힣]+[시군구]?\s*[가-힣0-9]*[로길동읍면]\s*\d*(?:-\d+)?(?:번지)?"
                         r"(?:\s*\d+(?:동|호|층))*")),
    ("name", re.compile(r"(?<=이름[:\s])\s*[가-힣]{2,4}|(?<=성명[:\s])\s*[가-힣]{2,4}|(?<=name[:\s])\s*[A-Za-z][A-Za-z .]{1,30}", re.I)),
]
PRIORITY = {n: i for i, (n, _) in enumerate(PATTERNS)}
LABEL = {"rrn": "주민번호", "card": "카드번호", "biz": "사업자번호", "mobile": "휴대폰", "phone": "전화", "email": "이메일", "ip": "IP", "address": "주소", "name": "이름"}


def luhn(num):
    d = [int(c) for c in re.sub(r"\D", "", num)]
    if len(d) < 13: return False
    s = 0
    for i, x in enumerate(reversed(d)):
        if i % 2: x = x * 2 - 9 if x * 2 > 9 else x * 2
        s += x
    return s % 10 == 0


def rrn_checksum(digits):
    w = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
    return (11 - sum(int(a) * b for a, b in zip(digits[:12], w)) % 11) % 10 == int(digits[12])


def biz_valid(s):
    d = [int(c) for c in re.sub(r"\D", "", s)]
    w = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    t = sum(a * b for a, b in zip(d[:9], w)) + d[8] * 5 // 10
    return (10 - t % 10) % 10 == d[9]


def _valid_date(yy, mm, dd, g):
    century = 1900 if g in "1256" else 2000 if g in "3478" else None
    if century is None: return False
    try:
        date(century + int(yy), int(mm), int(dd)); return True
    except ValueError:
        return False


def find(text, kinds=None):
    """[(start, end, kind, note)] — 겹치면 우선순위가 높은 것 하나만 남긴다."""
    hits = []
    for kind, rx in PATTERNS:
        if kinds and kind not in kinds: continue
        for m in rx.finditer(text):
            note = ""
            if kind == "rrn":
                yy, mm, dd, g, rest = m.groups()
                if not _valid_date(yy, mm, dd, g): continue
                note = "체크섬 일치" if rrn_checksum(yy + mm + dd + g + rest) else "형식만 일치"
            elif kind == "card" and not luhn(m.group()): continue
            elif kind == "biz" and not biz_valid(m.group()): continue
            elif kind == "ip":
                try: ipaddress.ip_address(m.group())
                except ValueError: continue
            s, e = m.start(), m.end()
            if kind == "name": 
                raw = m.group(); s += len(raw) - len(raw.lstrip()); 
            hits.append((s, e, kind, note))
    hits.sort(key=lambda h: (h[0], PRIORITY[h[2]]))
    out = []
    for h in hits:
        if out and h[0] < out[-1][1]:
            if PRIORITY[h[2]] < PRIORITY[out[-1][2]] and h[1] - h[0] >= out[-1][1] - out[-1][0]:
                out[-1] = h
            continue
        out.append(h)
    return out
