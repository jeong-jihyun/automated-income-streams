import copy
import json
import os
import pytest
from quizgen import bank, grade, param, render, select
from quizgen.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "bank.json")
B = bank.load(S)


def test_bank_validation(tmp_path):
    for bad, msg in (({"id": "x"}, "정보 부족"),):
        with pytest.raises(bank.QuizError, match=msg): bank.check_item(bad)
    it = copy.deepcopy(B[0])
    it["answer"] = 9; pytest.raises(bank.QuizError, bank.check_item, it)
    it = copy.deepcopy(B[0]); it["choices"] = ["a", "A"]
    with pytest.raises(bank.QuizError, match="같은 보기"): bank.check_item(it)
    it = copy.deepcopy(B[0]); it["difficulty"] = 5
    with pytest.raises(bank.QuizError, match="난이도"): bank.check_item(it)
    dup = tmp_path / "d.json"; dup.write_text(json.dumps([B[0], dict(B[0], id="other")]), encoding="utf-8")
    with pytest.raises(bank.QuizError, match="중복"): bank.load(str(dup))
    dup.write_text("[", encoding="utf-8")
    with pytest.raises(bank.QuizError, match="JSON"): bank.load(str(dup))


def test_math_questions_are_always_correct():
    for g in range(1, 7):
        for i in range(60):
            q = param.make(g, 5, i); bank.check_item(q)
            a, op, b, _, _ = q["q"].split(); a, b = int(a), int(b)
            exp = {"+": a + b, "-": a - b, "×": a * b, "÷": a // b}[op]
            assert int(q["choices"][q["answer"]]) == exp and (op != "÷" or a % b == 0) and exp >= 0
    assert param.make(3, 1, 0) == param.make(3, 1, 0)
    with pytest.raises(ValueError): param.make(9, 1)


def test_weak_topics_get_picked_more():
    prof = {"topics": {"분수": {"right": 0, "total": 10}, "도형": {"right": 10, "total": 10}}}
    cnt = {"분수": 0, "도형": 0, "시간": 0}
    for seed in range(300):
        cnt[select.pick(B, prof, 1, 4, seed)[0]["topic"]] += 1
    assert cnt["분수"] > cnt["도형"] * 2 and select.weak_topics(prof) == ["분수"]


def test_pick_rules():
    a, b = select.pick(B, {}, 4, 4, 3), select.pick(B, {}, 4, 4, 3)
    assert [x["id"] for x in a] == [x["id"] for x in b] and len({x["id"] for x in a}) == 4 and all(x["grade"] == 4 for x in a)
    assert len(select.pick(B, {}, 50, 4, 1)) == 6 and select.pick(B, {}, 3, 1, 1) == []
    assert "w1" not in [x["id"] for x in select.pick(B, {}, 6, 4, 1, recent_ok=["w1"])]
    with pytest.raises(ValueError): select.pick(B, {}, 0, 4, 1)


def test_grading_updates_profile():
    quiz = B[:3]; prof = {}
    r = grade.grade(quiz, [quiz[0]["answer"], 3, None], prof)
    assert r["right"] == 1 and len(r["wrong"]) == 2 and r["wrong"][1]["yours"] is None
    assert prof["topics"]["분수"] == {"right": 1, "total": 2} and prof["topics"]["도형"]["total"] == 1
    with pytest.raises(ValueError, match="개수"): grade.grade(quiz, [0], prof)


def test_shuffle_keeps_answer_and_escape():
    q = dict(B[0], q="<script>alert(1)</script> 1+1?")
    s = render.shuffle_choices(q, 7); assert s["choices"][s["answer"]] == q["choices"][q["answer"]] and sorted(s["choices"]) == sorted(q["choices"])
    h = render.worksheet([s]); assert "<script>" not in h and "&lt;script&gt;" in h
    assert "정답" in render.answer_sheet([s])


def test_ai_items_filtered():
    good = dict(B[0], id="n1", q="새 질문 1+1?", choices=["2", "3"], answer=0, explanation="1+1=2")
    bad_dup = dict(B[0], id="n2")                                                    # 질문 중복
    bad_ans = dict(good, id="n3", q="다른 질문 2+2?", choices=["4", "5"], answer=1, explanation="틀린 정답")
    ok, rej = bank.accept_ai_items(B, [good, bad_dup, bad_ans, {"id": "n4"}], verify=lambda it: it["choices"][it["answer"]] in ("2", "4") and "틀린" not in it["explanation"])
    assert [x["id"] for x in ok] == ["n1"] and {r[0] for r in rej} == {"n2", "n3", "n4"}


def test_cli(tmp_path, capsys):
    out, prof = str(tmp_path / "o"), str(tmp_path / "p.json")
    assert main(["make", S, "--grade", "4", "--n", "3", "--math", "2", "--out", out]) == 0
    quiz = json.load(open(os.path.join(out, "quiz.json"), encoding="utf-8")); assert len(quiz) == 5 and os.path.exists(os.path.join(out, "worksheet.html"))
    ans = ",".join(str(q["answer"]) for q in quiz)
    assert main(["grade", os.path.join(out, "quiz.json"), ans, "--profile", prof]) == 0 and "5/5" in capsys.readouterr().out
    assert main(["make", S, "--grade", "1", "--out", out]) == 2 and main(["grade", os.path.join(out, "quiz.json"), "1", "--profile", prof]) == 2
