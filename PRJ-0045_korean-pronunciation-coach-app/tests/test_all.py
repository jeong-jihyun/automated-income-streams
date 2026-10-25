import pytest
from coach import compare, g2p, hangul
from coach.cli import main


def test_decompose_compose():
    assert hangul.decompose("값") == [["ㄱ", "ㅏ", "ㅄ"]] and hangul.compose(hangul.decompose("한글")) == "한글"
    assert hangul.jamo("가a") == ["ㄱ", "ㅏ"]


@pytest.mark.parametrize("w,p", [("좋다", "조타"), ("밥을", "바블"), ("꽃이", "꼬치"), ("값이", "갑시"), ("국물", "궁물"), ("축하", "추카"), ("한국말", "한궁말"), ("종로", "종노"), ("부엌", "부억"), ("앉다", "안다")])
def test_pronounce_known(w, p):
    assert g2p.pronounce(w) == p


def test_pronounce_keeps_plain():
    assert g2p.pronounce("안녕하세요") == "안녕하세요" and g2p.pronounce("") == ""


def test_perfect_match_scores_100():
    r = compare.compare("좋다", "조타"); assert r["score"] == 100 and not r["diffs"] and r["same_as_spelling"] is False
    assert compare.compare("안녕하세요", "안녕하세요")["score"] == 100


def test_spelling_pronunciation_flags():
    r = compare.compare("국물", "국물"); assert r["score"] < 100 and r["diffs"]              # 소리 나는 대로(궁물)와 다름


def test_vowel_tip_korean_and_english():
    r = compare.compare("어머니", "오머니"); d = r["diffs"][0]
    assert d["want"] == "ㅓ" and d["got"] == "ㅗ" and "입을 크게" in d["tip"] and "uh" in d["tip_en"]


def test_aspirated_tip():
    d = compare.compare("파도", "바도")["diffs"][0]; assert (d["want"], d["got"]) == ("ㅍ", "ㅂ") and "세게" in d["tip"]


def test_missing_and_extra():
    kinds = {d["kind"] for d in compare.compare("안녕하세요", "안녕세요")["diffs"]}; assert "빠짐" in kinds
    assert "더 들어감" in {d["kind"] for d in compare.compare("안녕", "안녕하")["diffs"]}


def test_empty_heard_and_bad_target():
    r = compare.compare("안녕", "  "); assert r["empty"] and r["score"] == 0
    with pytest.raises(ValueError): compare.compare("hello", "x")


def test_note_always_present_and_cli(capsys):
    assert "높낮이·길이·억양은 평가하지 못합니다" in compare.compare("안녕", "안녕")["note"]
    assert main(["어머니", "오머니"]) == 0
    out = capsys.readouterr().out; assert "팁:" in out and "Tip:" in out and "평가하지 못합니다" in out
    assert main(["abc", "x"]) == 2
