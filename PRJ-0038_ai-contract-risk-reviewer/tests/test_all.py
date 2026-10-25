import os
import pytest
from contractrev import clauses, report, rules
from contractrev.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "contract.txt")
T = open(S, encoding="utf-8").read()


def titles(r):
    return {(f["clause"], f["title"]) for f in r["findings"]}


def test_split_clauses():
    cs = clauses.split(T); assert len(cs) == 8 and cs[0]["no"] == "제1조" and "자동으로 갱신" in cs[1]["text"]
    assert clauses.split("1. 첫째 조항\n내용\n2. 둘째\n내용")[1]["no"] == "2." and clauses.split("그냥 문장")[0]["no"] == "전체" and clauses.split("  ") == []


def test_sample_findings():
    r = report.review(T); f = titles(r)
    for want in (("제2조", "자동 갱신"), ("제3조", "늦은 대금 지급"), ("제4조", "일방적 해지·변경"), ("제4조", "모호한 판단 문구"), ("제5조", "높은 비율의 위약금"),
                 ("제5조", "무제한 책임"), ("제6조", "저작권·지식재산권 귀속"), ("제7조", "기간 없는 비밀유지"), ("제8조", "관할 법원")):
        assert want in f, want
    assert report.review(T)["findings"][0]["level"] == "높음"                       # 높음이 먼저
    assert r["missing"] == [] and r["counts"]["높음"] >= 3


def test_numbers_are_checked_not_just_words():
    ok = clauses.split("제1조 (위약금)\n지연 시 계약금액의 10%를 위약금으로 한다.")[0]
    t = {f["title"] for f in rules.review_clause(ok)}; assert "위약금·손해배상 예정" in t and "높은 비율의 위약금" not in t
    ok2 = clauses.split("제1조 (대금)\n대금은 30일 이내에 지급한다.")[0]; assert "늦은 대금 지급" not in {f["title"] for f in rules.review_clause(ok2)}


def test_clean_contract_and_missing():
    r = report.review("제1조 (목적)\n물건을 판매한다.")
    assert r["findings"] == [] and set(r["missing"]) == {"계약 기간", "대금(금액)", "해지", "분쟁 해결"}
    md = report.markdown(r); assert "안전하다는 뜻은 아닙니다" in md and "빠진 것처럼" in md


def test_markdown_has_easy_text_and_disclaimer():
    md = report.markdown(report.review(T))
    assert "쉬운 설명:" in md and "물어볼 것:" in md and "법률 자문이 아닙니다" in md and md.index("[높음]") < md.index("[중간]")


def test_no_false_alarm_on_bilateral_clause():
    t = "제1조 (해지)\n양 당사자는 30일 전에 서면으로 통지하여 계약을 해지할 수 있다."
    assert report.review(t)["findings"] == []


def test_errors_and_cli(tmp_path, capsys):
    with pytest.raises(ValueError): report.review("  ")
    out = str(tmp_path / "r.md")
    assert main([S, "--out", out]) == 0 and "주의 조항 점검" in open(out, encoding="utf-8").read()
    assert main([str(tmp_path / "none.txt")]) == 2
    (tmp_path / "e.txt").write_text(" "); assert main([str(tmp_path / "e.txt")]) == 2
