"""MBTI 간이 검사 채점. 문항 JSON: [{"q": 질문, "axis": "EI", "pole": "E"}...], 답은 1~5(5=매우 그렇다)."""
AXES = ("EI", "SN", "TF", "JP")


class FortuneError(ValueError):
    pass


def score(questions, answers):
    if len(answers) != len(questions): raise FortuneError(f"답 {len(answers)}개, 문항 {len(questions)}개 — 개수가 다릅니다")
    tot = {a: 0 for a in AXES}
    cnt = {a: 0 for a in AXES}
    for q, a in zip(questions, answers):
        if q["axis"] not in AXES or q["pole"] not in q["axis"]: raise FortuneError(f"문항 설정 오류: {q}")
        if not isinstance(a, int) or not 1 <= a <= 5: raise FortuneError(f"답은 1~5 숫자여야 합니다: {a!r}")
        tot[q["axis"]] += (a - 3) * (1 if q["pole"] == q["axis"][0] else -1)       # 첫 글자 쪽이면 +, 반대쪽이면 −
        cnt[q["axis"]] += 1
    missing = [a for a in AXES if cnt[a] == 0]
    if missing: raise FortuneError("문항이 없는 축이 있습니다: " + ",".join(missing))
    letters, detail = "", {}
    for a in AXES:
        letters += a[0] if tot[a] > 0 else a[1] if tot[a] < 0 else "X"
        detail[a] = tot[a]
    return {"type": letters, "detail": detail, "complete": "X" not in letters}
