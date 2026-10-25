"""한글 글 처리 도구: 문장 나누기, 낱말 뽑기(조사 간단 제거). 형태소 분석기가 아닌 간이 방식."""
import re

JOSA = ("에서는", "에서", "으로", "에게", "까지", "부터", "처럼", "보다", "이랑", "한테", "은", "는", "이", "가", "을", "를", "에", "의", "와", "과", "도", "로", "만", "랑")
STOP = {"오늘", "하루", "정말", "너무", "그리고", "그래서", "그런데", "하지만", "때문", "생각", "있었다", "했다", "했는데", "같다", "그냥", "조금", "많이", "다시"}


def sentences(t):
    return [s.strip() for s in re.split(r"(?<=[.!?。])\s+|\n+", t) if len(s.strip()) >= 4]


def words(t):
    out = []
    for w in re.findall(r"[가-힣]{2,}|[A-Za-z]{3,}", t):
        for j in JOSA:
            if w.endswith(j) and len(w) - len(j) >= 2: w = w[:-len(j)]; break
        if w not in STOP: out.append(w.lower())
    return out
