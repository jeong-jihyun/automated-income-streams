import os, shutil, subprocess
import pytest
from gasagency import core
from gasagency.cli import main

CSV = os.path.join(os.path.dirname(__file__), "..", "sample", "requests.csv")


def test_read_excludes_bad_rows():
    ok, bad = core.read(CSV)
    assert [q["id"] for q in ok] == ["Q1", "Q2", "Q3"] and [n for n, _ in bad] == [5, 6]
    assert bad[0][1].startswith("지원하지 않는 작업")


def test_estimate_formula():
    ok, _ = core.read(CSV); e = {q["id"]: core.estimate(q) for q in ok}
    assert e["Q1"]["hours"] == 3 and e["Q2"]["hours"] == 4 + 2 + 2 and e["Q3"]["hours"] == round((3 + 4) * 1.3, 1)
    assert e["Q1"]["low"] < e["Q1"]["high"]


def test_risks_and_scopes():
    ok, _ = core.read(CSV); q = {x["id"]: x for x in ok}
    assert any("개인정보" in r for r in core.risks(q["Q2"])) and any("메일 발송" in r for r in core.risks(q["Q2"]))
    assert core.scopes(q["Q3"])[-1].endswith("script.external_request")
    assert not any("external_request" in s for s in core.scopes(q["Q1"]))


def test_rush_flag():
    ok, _ = core.read(CSV); assert any("급행" in r for r in core.risks(ok[2]))


def test_missing_column(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("id\n1\n", encoding="utf-8")
    with pytest.raises(ValueError):
        core.read(str(p))


def test_duplicate_id(tmp_path):
    p = tmp_path / "a.csv"; h = "id,client,task,sheets,external_api,personal_data,urgency\n"
    p.write_text(h + "1,a,dedupe,1,0,0,normal\n1,b,dedupe,1,0,0,normal\n", encoding="utf-8")
    ok, bad = core.read(str(p)); assert len(ok) == 1 and "중복" in bad[0][1]


def test_skeleton_texts_have_expected_calls():
    assert "ScriptApp.newTrigger" in core.skeleton("daily_trigger") and "MailApp.sendEmail" in core.skeleton("summary_mail")
    assert "onFormSubmit" in core.skeleton("form_to_sheet")


@pytest.mark.skipif(shutil.which("node") is None, reason="node 없음")
@pytest.mark.parametrize("task", sorted(core.BASE))
def test_skeleton_js_syntax(task, tmp_path):
    f = tmp_path / "a.js"; f.write_text(core.skeleton(task), encoding="utf-8")
    r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True); assert r.returncode == 0, r.stderr


def test_report_disclaimer():
    ok, bad = core.read(CSV); t = core.report(ok, bad)
    assert "예시 설정" in t and "[제외] 5행" in t


def test_cli(capsys):
    assert main(["quote", CSV]) == 0 and "Q1" in capsys.readouterr().out
    assert main(["gen", "dedupe"]) == 0 and "dedupeRows" in capsys.readouterr().out
    assert main(["quote", "nope.csv"]) == 2
