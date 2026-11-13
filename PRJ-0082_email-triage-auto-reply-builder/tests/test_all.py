import csv, io, os
import pytest
from mailtriage import core
from mailtriage.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample"); M, R = os.path.join(D, "mails.csv"), os.path.join(D, "rules.json")


def rows():
    mails, bad = core.read_mails(M); return {r["id"]: r for r in core.process(mails, core.load_rules(R))}, bad


def test_bad_rows_excluded():
    mails, bad = core.read_mails(M); assert len(mails) == 7 and bad == [(8, "보낸 사람 주소 오류")]


def test_classification_and_name():
    r, _ = rows(); assert r["1"]["category"] == "견적문의" and "kim님" in r["1"]["draft"]
    assert r["2"]["category"] == "배송문의" and r["6"]["category"] == "환불요청"


def test_urgent_priority():
    r, _ = rows(); assert r["2"]["priority"] == "높음" and r["1"]["priority"] == "보통"


def test_no_reply_to_automatic_mail():
    r, _ = rows(); assert r["3"]["draft"] == "" and "자동 발송" in r["3"]["note"] and r["8"]["draft"] == ""


def test_one_draft_per_sender():
    r, _ = rows(); assert r["1"]["draft"] and r["4"]["draft"] == "" and "중복" in r["4"]["note"]


def test_replied_list_blocks():
    mails, _ = core.read_mails(M); out = {x["id"]: x for x in core.process(mails, core.load_rules(R), ["kim@example.com"])}
    assert out["1"]["draft"] == ""


def test_unmatched_goes_to_human():
    r, _ = rows(); assert r["5"]["category"] == "기타" and "사람이 확인" in r["5"]["note"]


def test_csv_formula_guard():
    row = {"id": "1", "from": "=cmd@x.com", "category": "기타", "priority": "보통", "draft": "+1", "note": "@a"}
    parsed = list(csv.reader(io.StringIO(core.to_csv([row]))))[1]
    assert parsed[1] == "'=cmd@x.com" and parsed[4] == "'+1" and parsed[5] == "'@a"
    assert core.safe("=1+1") == "'=1+1" and core.safe("abc") == "abc"


def test_bad_rules(tmp_path):
    p = tmp_path / "r.json"; p.write_text('[{"category":"a"}]', encoding="utf-8")
    with pytest.raises(ValueError):
        core.load_rules(str(p))


def test_cli(capsys):
    assert main([M, R]) == 0 and "견적문의" in capsys.readouterr().out
    assert main(["nope.csv", R]) == 2
