"""CSV 읽기, 열 종류 판별, 집계, 개인정보 열 찾기, 주관식 키워드. 표준 라이브러리만 사용."""
import csv
import re
import statistics
from collections import Counter

PII_HINTS = ["이름", "성명", "이메일", "email", "메일", "전화", "연락처", "휴대폰", "주소", "name", "phone"]
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE = re.compile(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}")
STOP = {"그리고", "너무", "정말", "조금", "아주", "있어요", "좋았어요", "해요", "입니다", "이", "그", "더"}


class SurveyError(ValueError):
    pass


def load(path):
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            raw = list(csv.reader(f))
            header = raw[0] if raw else []
            rows = [dict(zip(header, r)) for r in raw[1:] if any(x.strip() for x in r)]
    except FileNotFoundError:
        raise SurveyError(f"파일이 없습니다: {path}")
    except UnicodeDecodeError:
        raise SurveyError("글자 인코딩이 UTF-8이 아닙니다 (엑셀에서 'CSV UTF-8'로 저장하세요)")
    cols = header
    if len(set(cols)) != len(cols) or not cols or any(not (c or "").strip() for c in cols):
        raise SurveyError("열 이름이 비었거나 중복입니다")
    if not rows:
        raise SurveyError("응답이 한 줄도 없습니다")
    return cols, rows


def to_num(v):
    try:
        return float(str(v).strip())
    except ValueError:
        return None


def column_type(values, max_choice=8):
    vals = [v.strip() for v in values if v is not None and v.strip() != ""]
    if not vals:
        return "empty"
    if all(to_num(v) is not None for v in vals):
        return "number"
    uniq = set(vals)
    if len(uniq) <= max_choice and len(uniq) < len(vals):
        return "choice"
    return "text"


def pii_columns(cols, rows):
    out = []
    for c in cols:
        vals = [r[c] or "" for r in rows]
        hint = any(h in c.lower() for h in PII_HINTS)
        hit = any(EMAIL.search(v) or PHONE.search(v) for v in vals)
        if hint or hit:
            out.append(c)
    return out


def keywords(values, top=5, min_len=2):
    cnt = Counter()
    for v in values:
        for w in re.findall(r"[가-힣A-Za-z0-9]+", v or ""):
            w = re.sub(r"(이|가|은|는|을|를|도|에|요)$", "", w) if len(w) > 2 else w
            if len(w) >= min_len and w not in STOP:
                cnt[w] += 1
    return [(w, n) for w, n in cnt.most_common(top) if n >= 1]


def analyze(cols, rows, drop_pii=True):
    pii = pii_columns(cols, rows)
    use = [c for c in cols if not (drop_pii and c in pii)]
    result = {"n": len(rows), "pii": pii, "dropped": pii if drop_pii else [], "columns": []}
    for c in use:
        raw = [r[c] or "" for r in rows]
        t = column_type(raw)
        item = {"name": c, "type": t, "answered": sum(1 for v in raw if v.strip()), "missing": sum(1 for v in raw if not v.strip())}
        if t == "number":
            nums = [to_num(v) for v in raw if v.strip()]
            item.update(mean=round(statistics.mean(nums), 2), median=statistics.median(nums), min=min(nums), max=max(nums),
                        dist=sorted(Counter(int(x) if x == int(x) else x for x in nums).items()))
        elif t == "choice":
            item["dist"] = Counter(v.strip() for v in raw if v.strip()).most_common()
        elif t == "text":
            item["keywords"] = keywords(raw)
        result["columns"].append(item)
    return result
