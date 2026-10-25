"""수학 계산 문제를 학년별로 즉석 생성(정답과 해설을 계산으로 만든다 → 틀린 정답이 나올 수 없음)."""
import random

RANGE = {1: (1, 10), 2: (1, 20), 3: (10, 100), 4: (10, 500), 5: (10, 1000), 6: (10, 2000)}
OPS = {1: "+-", 2: "+-", 3: "+-x", 4: "+-x", 5: "+-x/", 6: "+-x/"}


def make(grade, seed, idx=0):
    if grade not in RANGE: raise ValueError("학년은 1~6")
    rng = random.Random(f"{seed}-{grade}-{idx}")
    lo, hi = RANGE[grade]; op = rng.choice(OPS[grade]); a, b = rng.randint(lo, hi), rng.randint(lo, hi)
    if op == "-" and b > a: a, b = b, a
    if op == "x": a, b = rng.randint(2, 9 if grade < 5 else 30), rng.randint(2, 9 if grade < 5 else 20)
    if op == "/": b = rng.randint(2, 12); a = b * rng.randint(2, 12 if grade < 6 else 40)
    ans = {"+": a + b, "-": a - b, "x": a * b, "/": a // b}[op]
    sym = {"x": "×", "/": "÷"}.get(op, op)
    wrong = {ans + d for d in (1, -1, 10, -10, 2) if ans + d >= 0} - {ans}
    wrong = sorted(wrong)[:3]
    choices = [ans] + wrong; rng.shuffle(choices)
    return {"id": f"gen-{grade}-{seed}-{idx}", "topic": "계산-" + {"+": "덧셈", "-": "뺄셈", "x": "곱셈", "/": "나눗셈"}[op], "grade": grade, "difficulty": 1 if grade <= 2 else 2,
            "q": f"{a} {sym} {b} = ?", "choices": [str(c) for c in choices], "answer": choices.index(ans), "explanation": f"{a} {sym} {b} = {ans}"}
