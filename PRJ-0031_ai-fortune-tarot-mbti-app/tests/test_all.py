import datetime
import json
import os
import pytest
from fortune import guard, mbti, reading, saju, tarot
from fortune.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
Q = json.load(open(os.path.join(S, "mbti_questions.json"), encoding="utf-8"))


def test_mbti_scoring_and_ties():
    r = mbti.score(Q, [5, 1, 5, 1, 1, 5, 5, 1]); assert r["type"] == "ESFJ" and r["complete"]
    r = mbti.score(Q, [1, 5, 1, 5, 5, 1, 1, 5]); assert r["type"] == "INTP"
    r = mbti.score(Q, [3] * 8); assert r["type"] == "XXXX" and not r["complete"]


def test_mbti_errors():
    with pytest.raises(mbti.FortuneError, match="개수"): mbti.score(Q, [3])
    with pytest.raises(mbti.FortuneError, match="1~5"): mbti.score(Q, [3, 3, 3, 3, 3, 3, 3, 9])
    with pytest.raises(mbti.FortuneError, match="축"): mbti.score(Q[:2], [3, 3])


def test_tarot_seed_and_no_duplicates():
    a, b = tarot.draw(3, 7), tarot.draw(3, 7)
    assert a == b and len({c["card"] for c in a}) == 3 and [c["position"] for c in a] == ["과거", "현재", "앞으로의 흐름"]
    for seed in range(200): assert len({c["card"] for c in tarot.draw(3, seed)}) == 3
    with pytest.raises(ValueError): tarot.draw(5)
    assert len(tarot.CARDS) == 22


def test_saju_known_dates():
    p = saju.pillars(datetime.date(2000, 1, 1))
    assert p["day"]["name"] == "무오" and p["year"]["name"] == "기묘"          # 2000-01-01은 입춘 전 → 1999 기묘년, 일진 무오
    assert saju.pillars(datetime.date(2000, 2, 4))["year"]["name"] == "경진"
    assert saju.pillars(datetime.date(1984, 2, 5))["year"]["name"] == "갑자"
    h = saju.pillars(datetime.date(2000, 1, 1), 23)["hour"]["name"]; assert h[1] == "자"
    assert sum(saju.elements(saju.pillars(datetime.date(2000, 1, 1), 12)).values()) == 6
    with pytest.raises(ValueError): saju.pillars(datetime.date(1800, 1, 1))
    with pytest.raises(ValueError): saju.pillars(datetime.date(2000, 1, 1), 24)


def test_guard_crisis_and_decisions():
    assert guard.check_question("죽고 싶어요 올해 운세?")[0] == "crisis" and "109" in guard.check_question("자살하고 싶다")[1]
    assert guard.check_question("암 수술 받아도 낫을까요")[0] == "decision"
    assert guard.check_question("이 코인 사도 될까요 투자 운")[0] == "decision"
    assert guard.check_question("올해 연애운이 궁금해요")[0] == "ok"


def test_consult_template_has_disclaimer_and_no_absolutes():
    r = reading.consult("연애운", tarot.draw(3, 1), {"type": "INTP"}, {"목": 3, "화": 1, "토": 1, "금": 0, "수": 1})
    assert r["source"] == "template" and "재미" in r["text"] and "INTP" in r["text"] and not guard.ABSOLUTE.search(r["text"])
    assert "'목' 기운" in r["text"]


def test_crisis_never_reaches_llm():
    called = []
    r = reading.consult("죽고 싶다", llm=lambda p: called.append(p) or "x")
    assert r["kind"] == "crisis" and not called


def test_llm_output_is_filtered_and_fallbacks():
    bad = lambda p: "당신은 반드시 큰 병에 걸립니다. 올해는 새로운 사람을 만날 가능성이 열려 있어요. 천천히 마음을 살펴보세요."
    r = reading.consult("연애운", llm=bad)
    assert r["source"] == "llm" and r["removed"] == 1 and "반드시" not in r["text"] and "새로운 사람" in r["text"]
    allbad = reading.consult("운", llm=lambda p: "반드시 죽는다. 100% 재앙이다.")
    assert allbad["source"].startswith("template") and "재앙" not in allbad["text"]
    def boom(p): raise RuntimeError("x")
    assert reading.consult("운", llm=boom)["source"] == "template(llm 오류)"


def test_cli(capsys):
    assert main(["mbti", os.path.join(S, "mbti_questions.json"), "5,1,5,1,1,5,5,1"]) == 0 and "ESFJ" in capsys.readouterr().out
    assert main(["tarot", "--n", "1", "--seed", "3"]) == 0 and "재미" in capsys.readouterr().out
    assert main(["saju", "2000-01-01", "--hour", "12"]) == 0 and "무오" in capsys.readouterr().out
    assert main(["saju", "2000-13-01"]) == 2 and main(["mbti", os.path.join(S, "mbti_questions.json"), "1,2"]) == 2
