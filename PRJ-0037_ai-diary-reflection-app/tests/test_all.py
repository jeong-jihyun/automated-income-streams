import json
import os
import pytest
from diaryrefl import reflect, store, summary, text
from diaryrefl.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "diary.json")
D = json.load(open(S, encoding="utf-8"))


def test_text_tools():
    assert text.words("러닝을 했다. 회의에서 일정이") == ["러닝", "회의", "일정"]
    assert text.sentences("짧다. 이것은 충분히 긴 문장입니다. 또 다른 문장이에요!") == ["이것은 충분히 긴 문장입니다.", "또 다른 문장이에요!"]


def test_summary_picks_keyword_sentences_in_order():
    t = "일정이 밀려서 걱정이다. 점심은 김치찌개였다. 일정 조정을 이야기했다. 일정이 정리돼 안심했다."
    s = summary.summarize(t, 2); assert len(s) == 2 and all("일정" in x for x in s) and t.index(s[0]) < t.index(s[1])
    assert summary.summarize("한 문장만 있습니다.", 3) == ["한 문장만 있습니다."]


def test_store_rules():
    d = []
    store.add(d, "2026-10-01", "첫 글입니다", 3); store.add(d, "2026-10-01", "이어 쓰기", 4)
    assert len(d) == 1 and "이어 쓰기" in d[0]["body"] and d[0]["mood"] == 4
    for args, msg in ((("2026-13-01", "x"), "날짜"), (("2026-10-02", " "), "비었"), (("2026-10-02", "x", 9), "1~5")):
        with pytest.raises(store.DiaryError, match=msg): store.add(d, *args)


def test_reflection_numbers():
    r = reflect.reflect(D, "2026-10-19", "2026-10-25")
    assert r["days"] == 5 and r["span"] == 7 and r["avg_mood"] == 3.4 and r["best"] == "2026-10-22" and r["worst"] == "2026-10-19"
    assert r["trend"] == "올라가는 중" and "일정" in r["keywords"] and "기록률 71%" in r["text"] and "진단하지 않습니다" in r["text"]


def test_empty_and_bad_period():
    assert reflect.reflect(D, "2026-01-01", "2026-01-07")["empty"]
    with pytest.raises(ValueError): reflect.reflect(D, "2026-10-25", "2026-10-19")


def test_crisis_shows_support_and_skips_ai():
    d = [{"date": "2026-10-20", "body": "요즘 너무 힘들어서 죽고 싶다는 생각이 든다.", "mood": 1}]
    called = []
    r = reflect.reflect(d, "2026-10-20", "2026-10-20", llm=lambda p: called.append(p) or "x" * 50)
    assert r["crisis"] and "109" in r["text"] and not called and "AI 회고" not in r["text"]


def test_llm_hook_and_failures():
    ok = reflect.reflect(D, "2026-10-19", "2026-10-25", llm=lambda p: "이번 주는 힘든 날도 있었지만 운동으로 기운을 찾았어요. 천천히 이어 가면 좋겠어요.")
    assert "[AI 회고]" in ok["text"]
    def boom(p): raise RuntimeError("x")
    assert "AI 회고" not in reflect.reflect(D, "2026-10-19", "2026-10-25", llm=boom)["text"]
    assert "AI 회고" not in reflect.reflect(D, "2026-10-19", "2026-10-25", llm=lambda p: "짧음")["text"]


def test_cli(tmp_path, capsys):
    f = str(tmp_path / "d.json")
    assert main(["--file", f, "add", "오늘은 산책을 했다. 기분이 좋았다.", "--date", "2026-10-25", "--mood", "4"]) == 0
    assert main(["--file", f, "summary", "2026-10-25"]) == 0 and "산책" in capsys.readouterr().out
    assert main(["--file", f, "reflect", "2026-10-19", "2026-10-25"]) == 0 and "1일 기록" in capsys.readouterr().out
    assert main(["--file", f, "summary", "2020-01-01"]) == 2
    open(f, "w").write("{"); assert main(["--file", f, "reflect", "2026-10-19", "2026-10-25"]) == 2
