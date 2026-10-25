import os
import pytest
from tutor import grammar, session, wer
from tutor.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "scenarios.json")


def rules(t):
    return [(g["rule"], g["suggest"]) for g in grammar.check(t)]


def test_wer_basic():
    r, ops = wer.wer("I have a cup of coffee", "I have a cup of coffee"); assert r == 0 and ops == []
    r, ops = wer.wer("I have a cup of coffee", "I had a coffee"); assert ("바뀜", "have", "had") in ops and ("빠짐", "cup", "") in ops and ("빠짐", "of", "") in ops and r == pytest.approx(3 / 6)
    r, ops = wer.wer("hello", "hello world"); assert ops == [("더함", "", "world")] and r == 1.0
    assert wer.wer("Hello, World!", "hello world")[0] == 0                       # 대소문자·문장부호 무시
    with pytest.raises(ValueError): wer.wer("", "x")


def test_third_person_and_be():
    assert ("3인칭 단수", "He goes") in rules("He go to school.") and ("be동사", "I am") in rules("I is happy.")
    assert ("be동사", "They are") in rules("They is late.") and ("be동사", "She is") in rules("She are kind.")
    assert rules("He goes to school.") == []


def test_articles():
    assert ("관사", "an apple") in rules("I ate a apple.") and ("관사", "a book") in rules("I read an book.")
    assert rules("It is a university.") == [] and rules("It takes an hour.") == [] and rules("He is an honest man.") == []
    assert ("관사", "an umbrella") not in rules("I have an umbrella.")


def test_misc_rules():
    r = [x["rule"] for x in grammar.check("i like it more better")]
    assert "대문자 I" in r and "비교급" in r and "문장 끝" in r
    assert "문장 시작" in [x["rule"] for x in grammar.check("hello there.")] and "공백" in [x["rule"] for x in grammar.check("Hello  there.")]
    assert grammar.check("It is fine.") == [] and grammar.check("I'm fine.") == []


def test_practice_feedback():
    r = session.practice("Can I have a cup of coffee, please?", "can i have a coffee please", "2026-10-25")
    assert 50 <= r["score"] < 90 and any("cup" in t for t in r["tips"]) and r["date"] == "2026-10-25"
    assert session.practice("Hello there", "hello there")["grade"] == "아주 좋아요!"


def test_transcribe_hook_and_empty(tmp_path):
    f = tmp_path / "a.wav"; f.write_bytes(b"x")
    assert session.transcribe_and_practice("Hello", str(f), lambda p: "hello")["score"] == 100
    assert "error" in session.transcribe_and_practice("Hello", str(f), lambda p: "  ")
    with pytest.raises(FileNotFoundError): session.transcribe_and_practice("Hello", str(tmp_path / "no.wav"), lambda p: "x")


def test_log_and_progress(tmp_path):
    f = str(tmp_path / "log.json"); assert session.progress(f) == {"count": 0}
    for s, d in (("hello there", "2026-10-24"), ("hello", "2026-10-25")):
        session.log(f, session.practice("Hello there", s, d))
    p = session.progress(f); assert p["count"] == 2 and p["avg"] == 75 and p["days"] == {"2026-10-24": 100, "2026-10-25": 50} and p["weak"] == ["Hello there"]


def test_cli(tmp_path, capsys):
    lg = str(tmp_path / "l.json")
    assert main(["check", "He go to school"]) == 0 and "3인칭" in capsys.readouterr().out
    assert main(["drill", S, "--id", "2", "--said", "where is the subway station", "--log", lg]) == 0 and "점" in capsys.readouterr().out
    assert main(["progress", lg]) == 0 and "1번 연습" in capsys.readouterr().out
    assert main(["drill", S, "--id", "9", "--said", "x"]) == 2
