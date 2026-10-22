import os
from datetime import date
import pytest
from faq_kb import index as ix
from faq_kb.cli import main

CSV = os.path.join(os.path.dirname(__file__), "..", "sample", "faq.csv")
DOCS = ix.load_csv(CSV)
IDX = ix.Index(DOCS)


def top(q, dept="all"):
    r = IDX.search(q, dept); return r[0][0]["id"] if r else None


@pytest.mark.parametrize("q,want", [("연차 신청은 어떻게 해요?", "1"), ("연차를 쓰고 싶어요", "1"), ("법인카드 영수증 제출 기한", "2"),
                                    ("재택근무 하려면", "3"), ("VPN이 안돼요", "5"), ("경비 정산", "2")])
def test_korean_queries_with_particles(q, want):
    assert top(q) == want


def test_no_answer_returns_empty():
    assert IDX.search("회식 장소 추천") == [] and IDX.search("") == []


def test_department_visibility():
    assert top("급여명세서 어디서 확인") is None                    # 일반 직원에겐 hr 전용 문서가 안 보임
    assert top("급여명세서 어디서 확인", "hr") == "4"


def test_tokenizer():
    t = ix.tokens("연차는 어떻게 신청하나요?")
    assert "연차는" in t and "연차" in t and "신청하나요" in t and "어떻게" not in t and "VPN".lower() in ix.tokens("VPN 접속")


def test_stale_missing_duplicates():
    assert ix.stale(DOCS, date(2031, 3, 1)) == ["3"] and ix.stale(DOCS, date(2031, 3, 1), days=20) == ["1", "3", "4"]
    d2 = DOCS + [{"id": "9", "question": "연차는 어떻게 신청하나요", "answer": "x", "tags": [], "dept": "all", "updated": ""}]
    assert ("1", "9") in ix.near_duplicates(d2) and ix.missing_dates(d2) == ["9"] and ix.near_duplicates(DOCS) == []


def test_csv_errors(tmp_path):
    for text, msg in [("id,question\n1,a\n", "id,question,answer"), ("id,question,answer\n1,a,b\n1,c,d\n", "중복"),
                      ("id,question,answer\n1,,b\n", "비었"), ("id,question,answer,updated\n1,a,b,2031/1/1\n", "YYYY-MM-DD")]:
        f = tmp_path / "f.csv"; f.write_text(text, encoding="utf-8")
        with pytest.raises(ix.KbError, match=msg): ix.load_csv(str(f))
    with pytest.raises(ix.KbError): ix.load_csv(str(tmp_path / "none.csv"))


def test_cli(tmp_path, capsys):
    idx = str(tmp_path / "k.json")
    assert main(["build", "--csv", CSV, "--index", idx]) == 0
    assert main(["ask", "연차 신청 방법", "--index", idx]) == 0 and "그룹웨어" in capsys.readouterr().out
    assert main(["ask", "점심 메뉴", "--index", idx]) == 0 and "찾지 못했습니다" in capsys.readouterr().out
    assert main(["check", "--csv", CSV, "--today", "2031-03-01"]) == 0 and "3번" in capsys.readouterr().out
    assert main(["ask", "x", "--index", str(tmp_path / "no.json")]) == 2
