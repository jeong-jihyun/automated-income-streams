import os, json
import pytest
from connect import post
from connect.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "facts.json")
F = post.load(S)


def test_make_has_disclosure_top_and_bottom_and_cons():
    t = post.make(F)
    assert t.startswith(post.DISCLOSURE) and t.rstrip().endswith(post.DISCLOSURE) and "## 아쉬운 점" in t and "14일 써 본 후기" in t and "79,000원" in t


@pytest.mark.parametrize("k,msg", [("use_days", "직접 사용한 일수"), ("pros", "장점"), ("cons", "아쉬운 점"), ("link", "빠진 항목"), ("who_for", "빠진 항목")])
def test_make_requires_real_experience(k, msg):
    f = dict(F); f.pop(k)
    with pytest.raises(post.PostError, match=msg): post.make(f)


def test_zero_days_refused():
    with pytest.raises(post.PostError): post.make({**F, "use_days": 0})


def test_check_generated_post_only_needs_photos_and_length():
    r = post.check(post.make(F), photos=3); kinds = [k for k, _ in r]
    assert "고지" not in kinds and "과장" not in kinds and "균형" not in kinds


def test_check_finds_problems():
    r = post.check("이 제품은 무조건 최고의 역대급! 완치 효과 보장", photos=1); kinds = [k for k, _ in r]
    assert kinds.count("과장") >= 4 and "고지" in kinds and "사진" in kinds and "분량" in kinds and "균형" in kinds


def test_disclosure_must_be_at_top():
    late = "가" * 300 + post.DISCLOSURE; assert any(k == "고지" for k, _ in post.check(late, 3))


def test_load_error():
    with pytest.raises(post.PostError): post.load("/nonexistent.json")


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "p.md")
    assert main(["make", S, "--out", out]) == 0 and main(["check", out, "--photos", "3"]) in (0, 1)
    bad = tmp_path / "b.md"; bad.write_text("무조건 좋아요"); assert main(["check", str(bad)]) == 1
    f = tmp_path / "f.json"; f.write_text(json.dumps({"product": "x"})); assert main(["make", str(f)]) == 2
