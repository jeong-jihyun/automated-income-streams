"""자막으로 구간 나누기·핵심 구간 고르기(낱말 중요도 TF-IDF 방식, AI 아님). 영상 내용을 직접 보지는 않는다."""
import math
import re
from collections import Counter

JOSA = ("에서는", "에서", "으로", "에게", "까지", "부터", "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "도", "로", "만")
STOP = {"그리고", "그래서", "그런데", "하지만", "이제", "여러분", "오늘", "그냥", "정말", "the", "and", "that", "this", "with", "for", "you", "are", "was"}


def words(t):
    out = []
    for w in re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", t):
        for j in JOSA:
            if w.endswith(j) and len(w) - len(j) >= 2: w = w[:-len(j)]; break
        if w.lower() not in STOP: out.append(w.lower())
    return out


def segments(cues, window=60):
    segs, cur = [], []
    start = cues[0][0]
    for c in cues:
        if c[0] - start >= window and cur:
            segs.append(cur); cur, start = [], c[0]
        cur.append(c)
    if cur: segs.append(cur)
    return [{"start": s[0][0], "end": s[-1][1], "cues": s, "text": " ".join(c[2] for c in s)} for s in segs]


def score(segs):
    n = len(segs); df = Counter(w for s in segs for w in set(words(s["text"])))
    for s in segs:
        tf = Counter(words(s["text"])); tot = sum(tf.values()) or 1
        s["tfidf"] = {w: (c / tot) * math.log((1 + n) / (1 + df[w])) + 1e-9 for w, c in tf.items()}
        s["score"] = sum(sorted(s["tfidf"].values(), reverse=True)[:5])
        s["title"] = " · ".join(w for w, _ in sorted(s["tfidf"].items(), key=lambda x: -x[1])[:3]) or "(내용 없음)"
        kw = set(w for w, _ in sorted(s["tfidf"].items(), key=lambda x: -x[1])[:5])
        s["key"] = max(s["cues"], key=lambda c: sum(1 for w in words(c[2]) if w in kw))[2]
    return segs


def highlights(segs, n=3, min_len=10, max_len=90):
    """점수 높은 구간 n개(시간순). 너무 짧은 구간은 제외, 너무 긴 구간은 앞쪽 max_len초만."""
    ok = [s for s in segs if s["end"] - s["start"] >= min_len]
    top = sorted(sorted(ok, key=lambda s: -s["score"])[:n], key=lambda s: s["start"])
    return [{"start": s["start"], "end": min(s["end"], s["start"] + max_len), "title": s["title"]} for s in top]


def summary(segs, k=3):
    top = sorted(sorted(segs, key=lambda s: -s["score"])[:k], key=lambda s: s["start"])
    return [s["key"] for s in top]
