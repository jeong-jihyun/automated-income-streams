"""의심 리뷰 표시(단정하지 않음): 똑같은 글, 하루에 몰린 5점, 너무 짧은 글. 의심 리뷰는 통계에서 따로 센다. 기준은 예시이며 검증되지 않았다."""
import re
from collections import Counter


def norm(t):
    return re.sub(r"[\W_]+", "", t.lower())


def flag(rows, burst=5):
    dup = Counter(norm(r["text"]) for r in rows)
    day5 = Counter(r["date"] for r in rows if r["rating"] == 5 and r["date"])
    out = []
    for r in rows:
        why = []
        if dup[norm(r["text"])] >= 2: why.append("똑같은 글이 여러 개")
        if r["date"] and day5[r["date"]] >= burst and r["rating"] == 5: why.append(f"같은 날 5점 {day5[r['date']]}개")
        if len(norm(r["text"])) < 6: why.append("너무 짧음")
        out.append(dict(r, suspect=why))
    return out
