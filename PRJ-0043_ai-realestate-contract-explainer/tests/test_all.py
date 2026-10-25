import os
import pytest
from realestate import analyze, registry, report
from realestate.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
T = open(os.path.join(S, "deungibu.txt"), encoding="utf-8").read()
REG = registry.parse(T)


def kinds(a):
    return [(f["kind"], f["level"]) for f in a["findings"]]


def test_won_parse():
    assert registry.won("채권최고액 금 96,000,000원") == 96000000 and registry.won("금액 없음") is None


def test_sections_and_entries():
    assert [e["no"] for e in REG["gap"]] == ["1", "2", "3"] and len(REG["eul"]) == 2
    with pytest.raises(registry.RegError): registry.parse("아무 글")


def test_cancelled_mortgage_not_counted():
    assert [e["no"] for e in REG["eul"]] == ["2", "4"]                         # 1번은 3번에서 말소됨
    a = analyze.analyze(REG); assert a["mortgage"] == 24000000 + 60000000


def test_findings_levels_and_owner():
    a = analyze.analyze(REG); assert a["owner"] == "이영희"
    k = kinds(a); assert ("가압류", "높음") in k and k.count(("근저당권", "참고")) == 2
    assert a["findings"][0]["level"] == "높음"                                   # 높은 위험이 먼저


def test_ratio_warning_threshold():
    a = analyze.analyze(REG, price=200_000_000, deposit=100_000_000)
    assert a["ratio"] == 0.92 and a["ratio_warn"] and any(f["kind"] == "빚+보증금 비율" for f in a["findings"])
    ok = analyze.analyze(REG, price=500_000_000, deposit=100_000_000); assert ok["ratio"] == 0.368 and not ok["ratio_warn"]
    edge = analyze.analyze(REG, price=120_000_000, deposit=0, ratio_limit=0.70); assert edge["ratio"] == 0.7 and not edge["ratio_warn"]


def test_owner_mismatch_is_top_level():
    a = analyze.analyze(REG, landlord="박민수"); assert a["owner_mismatch"] and a["findings"][0] == a["findings"][0] and kinds(a)[0] == ("소유자 불일치", "매우 높음")
    assert not analyze.analyze(REG, landlord="이 영희")["owner_mismatch"]


def test_serious_gap_entries():
    t = "【갑구】\n1 소유권이전 매매 소유자 김가나\n2 경매개시결정 등기\n3 신탁 수탁자 예시신탁\n【을구】\n1 전세권설정 존속기간 2년\n2 임차권등기명령 보증금 금 100,000,000원"
    k = kinds(analyze.analyze(registry.parse(t))); assert ("경매개시결정", "매우 높음") in k and ("신탁", "높음") in k and ("전세권", "중간") in k and ("임차권등기", "높음") in k


def test_special_terms_missing():
    miss = analyze.special_terms(open(os.path.join(S, "special_terms.txt"), encoding="utf-8").read())
    assert miss == ["근저당 말소·유지 조건", "잔금일 권리 유지"]
    assert len(analyze.special_terms("")) == 4


def test_report_text():
    md = report.markdown(analyze.analyze(REG, 200_000_000, 100_000_000), ["잔금일 권리 유지"])
    assert "자문이 아닙니다" in md and "92%" in md and "특약에서 빠진" in md and "84,000,000원" in md
    assert "안전하다는 뜻은 아닙니다" in report.markdown(analyze.analyze({"gap": [], "eul": []}))


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "r.md")
    assert main([os.path.join(S, "deungibu.txt"), "--price", "200000000", "--deposit", "100000000", "--landlord", "이영희", "--contract", os.path.join(S, "special_terms.txt"), "--out", out]) == 0
    assert "가압류" in open(out, encoding="utf-8").read()
    assert main([str(tmp_path / "none.txt")]) == 2
    (tmp_path / "x.txt").write_text("내용"); assert main([str(tmp_path / "x.txt")]) == 2
