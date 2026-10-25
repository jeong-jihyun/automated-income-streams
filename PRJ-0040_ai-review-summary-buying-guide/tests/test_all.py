import os
import pytest
from reviewsum import aspects, fake, guide, load
from reviewsum.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "reviews.csv")
ROWS, _ = load.load(S)


def test_load_and_skip(tmp_path):
    assert len(ROWS) == 13
    f = tmp_path / "r.csv"; f.write_text("rating,text,date\n5,좋아요 정말,2026-10-01\n9,범위 밖,2026-10-01\n4,,2026-10-01\n3,날짜 오류,2026-13-01\n", encoding="utf-8")
    rows, skipped = load.load(str(f)); assert len(rows) == 1 and skipped == [3, 4, 5]
    f.write_text("a,b\n1,2\n"); 
    with pytest.raises(load.ReviewError, match="rating"): load.load(str(f))
    f.write_text("rating,text\n"); 
    with pytest.raises(load.ReviewError, match="없습니다"): load.load(str(f))
    with pytest.raises(load.ReviewError): load.load(str(tmp_path / "none.csv"))


def test_suspect_marking():
    m = fake.flag(ROWS, burst=3)
    sus = [r for r in m if r["suspect"]]
    assert {r["text"] for r in sus} == {"최고예요 강추합니다 정말 좋아요", "좋아요", "짱"}
    assert any("똑같은 글" in w for r in sus for w in r["suspect"]) and any("너무 짧음" in w for r in sus for w in r["suspect"])
    assert not [r for r in m if r["text"].startswith("배송이 빠르고")][0]["suspect"]


def test_polarity_and_aspects():
    assert aspects.polarity("정말 좋고 만족해요") == "good" and aspects.polarity("별로고 실망이에요") == "bad" and aspects.polarity("그냥 그래요") == "neutral"
    a = aspects.analyze([r for r in ROWS if not fake.flag(ROWS, 3)[ROWS.index(r)]["suspect"]])
    assert len(a["소음"]["bad"]) == 2 and len(a["배송"]["good"]) == 2 and len(a["사이즈"]["bad"]) == 2


def test_guide_numbers_and_content():
    g = guide.build(ROWS); md = guide.markdown(g)
    assert g["total"] == 13 and g["suspect"] >= 3 and g["used"] == 13 - g["suspect"] and 1 <= g["avg"] <= 5 and sum(g["dist"].values()) == g["used"]
    assert any(p[0] == "배송" for p in g["pros"]) and any(c[0] == "소음" for c in g["cons"]) and any(c[0] == "사이즈" for c in g["cons"])
    assert "보증하지 않습니다" in md and "제휴" not in md and "좋다는 의견" in md


def test_affiliate_disclosure():
    assert "제휴 링크" in guide.markdown(guide.build(ROWS, affiliate=True))


def test_all_suspect_is_error():
    rows = [{"rating": 5, "text": "짱", "date": ""}] * 3
    with pytest.raises(ValueError, match="남는 리뷰"): guide.build(rows)


def test_min_support_filters_noise():
    g = guide.build(ROWS, min_support=3); assert all(n >= 3 for _, n, _ in g["pros"] + g["cons"])


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "g.md")
    assert main([S, "--out", out, "--affiliate"]) == 0 and "구매 가이드" in open(out, encoding="utf-8").read()
    assert main([str(tmp_path / "no.csv")]) == 2
