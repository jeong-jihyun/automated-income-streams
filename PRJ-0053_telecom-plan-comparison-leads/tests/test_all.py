import os
from datetime import date, datetime
import pytest
from telecom import plans, leads
from telecom.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "plans.json")
PL = plans.load(S); TODAY = date(2026, 10, 28)


def test_fits():
    assert plans.fits(PL[0], 10, 100) and not plans.fits(PL[0], 15, 0) and plans.fits(PL[1], 500, 0) and not plans.fits(PL[2], 5, 400) and plans.fits(PL[2], 5, 300)


def test_cost_discount_and_device():
    assert plans.cost(PL[0], 0.25, 0, 24) == {"monthly": 41250, "total": 990000} and plans.cost(PL[0], 0, 30000, 12) == {"monthly": 85000, "total": 1020000}


def test_rank_sorted_and_filtered():
    r = plans.rank(PL, need_gb=10, today=TODAY); assert [x["id"] for x in r] == ["c-mvno", "a-5g-light", "a-5g-max"]       # 8GB짜리는 제외
    assert plans.rank(PL, need_gb=100, need_call=1000, today=TODAY)[0]["id"] == "a-5g-max"


def test_stale_flag_and_render():
    r = plans.rank(PL, today=TODAY); b = next(x for x in r if x["id"] == "b-lte"); assert b["stale"] and b["age_days"] == 57
    t = plans.render(r); assert "⚠ 오래됨" in t and "30일 넘은" in t and "수수료를 받을 수 있습니다" in t and "무제한" in t
    assert "조건에 맞는 요금제가 없어요" in plans.render([])


def test_load_errors(tmp_path):
    with pytest.raises(plans.PlanError): plans.load(str(tmp_path / "n.json"))
    (tmp_path / "x.json").write_text('[{"id":"a"}]')
    with pytest.raises(plans.PlanError, match="carrier"): plans.load(str(tmp_path / "x.json"))
    (tmp_path / "y.json").write_text('[{"id":"a","carrier":"c","name":"n","monthly":-1,"price_date":"2026-01-01"}]')
    with pytest.raises(plans.PlanError, match="음수"): plans.load(str(tmp_path / "y.json"))


@pytest.mark.parametrize("kw,msg", [({"name": " "}, "이름"), ({"phone": "123"}, "번호"), ({"collect": False}, "수집"), ({"third": False}, "제3자"), ({"plan_id": ""}, "요금제")])
def test_lead_requires_consent_and_fields(kw, msg):
    base = dict(name="김철수", phone="010-1234-5678", collect=True, third=True, plan_id="a")
    with pytest.raises(leads.LeadError, match=msg): leads.validate(**{**base, **kw})


def test_save_mask_delete_and_permissions(tmp_path):
    f = str(tmp_path / "l.jsonl")
    with pytest.raises(leads.LeadError): leads.save(f, "김철수", "01012345678", "a")
    assert not os.path.exists(f)                                                            # 동의 없으면 파일도 안 만듦
    leads.save(f, "김철수", "010-1234-5678", "a", True, True, True, now=datetime(2026, 10, 28, 9, 0)); leads.save(f, "이영희", "01098765432", "b", True, True)
    assert oct(os.stat(f).st_mode)[-3:] == "600" and leads.mask("01012345678") == "010-****-5678"
    t = leads.report(f); assert "2건" in t and "김** 010-****-5678" in t and "1234" not in t and "광고수신 동의" in t
    assert leads.delete(f, "010-1234-5678") == 1 and len(leads.load(f)) == 1 and leads.delete(f, "01000000000") == 0


def test_cli(tmp_path, capsys):
    assert main(["compare", S, "--gb", "10", "--discount", "0.25", "--today", "2026-10-28"]) == 0 and "41,250원" in capsys.readouterr().out
    assert main(["compare", S, "--discount", "1.5"]) == 2
    f = str(tmp_path / "l.jsonl")
    assert main(["lead", f, "--name", "김철수", "--phone", "01012345678", "--plan", "a"]) == 2
    assert main(["lead", f, "--name", "김철수", "--phone", "01012345678", "--plan", "a", "--agree-collect", "--agree-third"]) == 0 and main(["report", f]) == 0 and main(["delete", f, "--phone", "01012345678"]) == 0
