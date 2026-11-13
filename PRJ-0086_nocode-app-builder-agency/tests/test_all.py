import json, os
import pytest
from nocodeplan import core
from nocodeplan.cli import main

SP = os.path.join(os.path.dirname(__file__), "..", "sample", "spec.json")


def chk():
    return core.check(core.load(SP))


def test_errors_found():
    err, _ = chk(); t = "\n".join(err)
    assert "없는 표 '직원'" in t and "알 수 없는 종류 'emoji'" in t and "화면 이름이 비었거나 중복: '수강생목록'" in t
    assert "없는 역할 'manager'" in t and "알 수 없는 동작 ['share']" in t and "없는 표 '없음'" in t


def test_unused_table_and_role_warned():
    _, w = chk(); t = "\n".join(w); assert "표 '메모'는 어떤 화면에서도" in t and "역할 'guest'가 볼 수 있는 화면이 없음" in t


def test_pii_list_to_many_roles():
    _, w = chk(); assert any("수강생목록" in x and "연락처" in x for x in w)


def test_needs_warnings():
    _, w = chk(); t = "\n".join(w)
    for k in ("결제 필요", "오프라인", "사용자 1500명", "외부 서비스 연동 4개"):
        assert k in t


def test_estimate_formula():
    d = {"tables": {"a": {"fields": {"x": "text", "y": "text"}}}, "screens": [{}, {}], "needs": {"payment": True, "external_apis": 1}}
    assert core.estimate(d)["hours"] == (2 + 1) + 6 + 6 + 2


def test_clean_spec_has_no_errors():
    d = {"app": "x", "roles": ["a"], "tables": {"t": {"fields": {"n": "text"}}}, "screens": [{"name": "s", "table": "t", "roles": ["a"], "actions": ["list"]}]}
    assert core.check(d) == ([], [])


def test_report_sections_and_disclaimer():
    t = core.report(core.load(SP)); assert "## 고쳐야 할 것" in t and "## 확인할 것" in t and "만들어 보지 않았고" in t


def test_load_errors(tmp_path):
    p = tmp_path / "a.json"; p.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        core.load(str(p))


def test_cli_exit_codes(tmp_path, capsys):
    assert main([SP]) == 1
    ok = tmp_path / "ok.json"; ok.write_text(json.dumps({"app": "x", "roles": ["a"], "tables": {"t": {}}, "screens": [{"name": "s", "table": "t", "roles": ["a"]}]}), encoding="utf-8")
    assert main([str(ok)]) == 0 and main(["nope.json"]) == 2
    bad = tmp_path / "bad.json"; bad.write_text("{", encoding="utf-8"); assert main([str(bad)]) == 2
