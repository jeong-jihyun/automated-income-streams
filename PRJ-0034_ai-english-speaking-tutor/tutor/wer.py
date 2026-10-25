"""말한 문장(받아쓰기 결과)과 목표 문장 비교: 단어 오류율(WER)과 틀린 곳 목록."""
import re


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def align(ref, hyp):
    r, h = words(ref), words(hyp)
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1): d[i][0] = i
    for j in range(len(h) + 1): d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (r[i - 1] != h[j - 1]))
    i, j, ops = len(r), len(h), []
    while i or j:
        if i and j and d[i][j] == d[i - 1][j - 1] + (r[i - 1] != h[j - 1]):
            if r[i - 1] != h[j - 1]: ops.append(("바뀜", r[i - 1], h[j - 1]))
            i, j = i - 1, j - 1
        elif i and d[i][j] == d[i - 1][j] + 1: ops.append(("빠짐", r[i - 1], "")); i -= 1
        else: ops.append(("더함", "", h[j - 1])); j -= 1
    return len(r), list(reversed(ops))


def wer(ref, hyp):
    n, ops = align(ref, hyp)
    if n == 0: raise ValueError("목표 문장이 비었습니다")
    return min(1.0, len(ops) / n), ops
