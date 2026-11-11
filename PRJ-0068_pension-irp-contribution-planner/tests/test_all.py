import json, os
import pytest
from pensionplan import core
from pensionplan.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); P = json.load(open(os.path.join(S, "profile.json"), encoding="utf-8"))


def test_zero_return_closed_form():
    p = dict(P, return_rate=0, post_return_rate=0, inflation=0, balance=0, age=40, retire_age=60, life_age=80, target_monthly_today=1_000_000)
    r = core.plan(p); assert r["need"] == 1_000_000 * 240 and r["required_monthly"] == 1_000_000     # 240개월 받으려면 240개월 모아야


def test_balance_alone_can_cover():
    p = dict(P, return_rate=0, post_return_rate=0, inflation=0, balance=10 ** 9); r = core.plan(p)
    assert r["required_monthly"] == 0 and r["shortfall"] == 0 and r["extra_monthly"] == 0


def test_required_reaches_need():
    r = core.plan(P); rm = core.mrate(P["return_rate"]); n = r["months"]
    got = P["balance"] * (1 + rm) ** n + r["required_monthly"] * core.fv_factor(rm, n)
    assert got >= r["need"] and got - r["need"] < core.fv_factor(rm, n)           # 올림 오차 1개월분 이내


def test_higher_return_needs_less():
    s = dict(core.scenarios(P)); assert s[0.02] < s[0.0] < s[-0.02]


def test_inflation_raises_target():
    assert core.plan(P)["target_then"] == round(2_000_000 * 1.02 ** 20)


def test_credit_rate_by_salary_and_limit():
    assert core.plan(P)["credit_rate"] == 0.132 and core.plan(dict(P, salary=40_000_000))["credit_rate"] == 0.165
    r = core.plan(dict(P, target_monthly_today=9_000_000)); assert any("한도" in w for w in r["warnings"]) and r["credit"] == round(9_000_000 * 0.132)


def test_warnings():
    r = core.plan(dict(P, retire_age=50, return_rate=0.12)); w = " ".join(r["warnings"])
    assert "55세" in w and "10%" in w


def test_invalid_inputs():
    for bad, msg in ((dict(P, retire_age=30), "순이어야"), (dict(P, salary=-1), "0 이상"), (dict(P, target_monthly_today=0), "0입니다"), ({k: v for k, v in P.items() if k != "age"}, "age")):
        with pytest.raises(ValueError, match=msg): core.plan(bad)


def test_config_override():
    assert core.plan(P, {"credit_rate_high": 0.2})["credit_rate"] == 0.2


def test_cli(capsys, tmp_path):
    assert main([os.path.join(S, "profile.json")]) == 0
    o = capsys.readouterr().out; assert "월 적립액" in o and "세무·투자 상담이 아닙니다" in o and "2%p" in o
    assert main([str(tmp_path / "none.json")]) == 2
