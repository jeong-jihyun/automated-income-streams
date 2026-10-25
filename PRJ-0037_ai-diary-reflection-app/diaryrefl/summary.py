"""일기 요약(문장 뽑기 방식, AI 아님). 자주 나온 낱말이 많이 든 문장을 골라 원래 순서로 보여 준다."""
from collections import Counter
from . import text


def summarize(t, k=2):
    ss = text.sentences(t)
    if len(ss) <= k: return ss
    freq = Counter(text.words(t))
    score = [sum(freq[w] for w in set(text.words(s))) / (1 + len(text.words(s)) ** 0.5) for s in ss]
    top = sorted(sorted(range(len(ss)), key=lambda i: -score[i])[:k])
    return [ss[i] for i in top]
