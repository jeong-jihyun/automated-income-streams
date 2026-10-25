import argparse
import json
import os
from . import bank, grade, param, render, select


def _profile(path):
    return json.load(open(path, encoding="utf-8")) if path and os.path.exists(path) else {}


def main(argv=None):
    p = argparse.ArgumentParser(prog="quizgen", description="학년·약점 맞춤 문제 만들기·채점")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("make"); s.add_argument("bank"); s.add_argument("--grade", type=int, required=True); s.add_argument("--n", type=int, default=5)
    s.add_argument("--seed", type=int, default=1); s.add_argument("--profile"); s.add_argument("--math", type=int, default=0, help="계산 문제 추가 개수"); s.add_argument("--out", required=True)
    s = sub.add_parser("grade"); s.add_argument("quiz"); s.add_argument("answers", help="쉼표로 구분한 보기 번호(0부터), 못 풀면 -"); s.add_argument("--profile", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "make":
            items = bank.load(a.bank); prof = _profile(a.profile)
            quiz = select.pick(items, prof, a.n, a.grade, a.seed) + [param.make(a.grade, a.seed, i) for i in range(a.math)]
            if not quiz: raise bank.QuizError(f"{a.grade}학년 문제가 없습니다")
            quiz = [render.shuffle_choices(q, a.seed) for q in quiz]
            os.makedirs(a.out, exist_ok=True)
            json.dump(quiz, open(os.path.join(a.out, "quiz.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            open(os.path.join(a.out, "worksheet.html"), "w", encoding="utf-8").write(render.worksheet(quiz))
            open(os.path.join(a.out, "answers.html"), "w", encoding="utf-8").write(render.answer_sheet(quiz))
            print(f"[완료] 문제 {len(quiz)}개 → {a.out} (약점 주제: {', '.join(select.weak_topics(prof)) or '아직 없음'})")
        else:
            quiz = json.load(open(a.quiz, encoding="utf-8")); prof = _profile(a.profile)
            ans = [None if x.strip() == "-" else int(x) for x in a.answers.split(",")]
            r = grade.grade(quiz, ans, prof); json.dump(prof, open(a.profile, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"{r['right']}/{r['total']} 정답")
            for w in r["wrong"]: print(f"- 틀림: {w['q']} (정답 {w['correct']}) {w['explanation']}")
        return 0
    except (bank.QuizError, ValueError, OSError, json.JSONDecodeError) as e:
        print(f"[오류] {e}"); return 2
