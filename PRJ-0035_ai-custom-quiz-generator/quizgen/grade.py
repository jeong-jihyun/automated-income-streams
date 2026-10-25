"""채점과 약점 기록 갱신."""


def grade(quiz, answers, profile):
    if len(answers) != len(quiz): raise ValueError(f"답 {len(answers)}개, 문제 {len(quiz)}개 — 개수가 다릅니다")
    right, wrong = 0, []
    topics = profile.setdefault("topics", {})
    for q, a in zip(quiz, answers):
        t = topics.setdefault(q["topic"], {"right": 0, "total": 0}); t["total"] += 1
        if a == q["answer"]: right += 1; t["right"] += 1
        else: wrong.append({"id": q["id"], "q": q["q"], "yours": None if a is None else q["choices"][a], "correct": q["choices"][q["answer"]], "explanation": q["explanation"]})
    return {"right": right, "total": len(quiz), "wrong": wrong}
