import datetime as dt, json, os
import pytest
from challenge import core
from challenge.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); T = dt.date(2026, 11, 12)
CFG = core.load_config(os.path.join(S, "config.json")); DEP = core.read_participants(os.path.join(S, "participants.csv"))
OK, BAD = core.verify(os.path.join(S, "logs.csv"), CFG, DEP, T); WHY = {(i, u): w for i, u, w in BAD}


def reasons(): return " | ".join(w for _, _, w in BAD)


def test_counts():
    assert len(OK["runner_a"]) == 4 and len(OK["runner_b"]) == 1 and len(OK["runner_c"]) == 1 and len(OK["runner_d"]) == 2


def test_rejections():
    r = reasons()
    for key in ("하루 1회", "인증 자료 중복", "속도", "최소 거리 또는 시간 미달", "챌린지 기간 밖", "미래 날짜", "참가자가 아님", "인증 자료(proof_id) 없음", "형식 오류"):
        assert key in r, key


def test_duplicate_proof_goes_to_second_user():
    assert any(u == "runner_b" and "중복(runner_a" in w for _, u, w in BAD)


def test_settlement_basic():
    rows, tot = core.settle(CFG, DEP, OK); d = {r["user"]: r for r in rows}
    assert d["runner_a"]["refund"] == 30000 and d["runner_a"]["achieved"] and d["runner_b"]["refund"] == 0


def test_money_is_conserved():
    for use in ("donate", "bonus_pool"):
        for part in (False, True):
            rows, t = core.settle(dict(CFG, forfeit_use=use, partial_refund=part), DEP, OK)
            assert t["deposits"] == t["refunds"] + t["fee"] + t["bonus"] + t["donate_or_remainder"] == 140000


def test_fee_and_donation_split():
    _, t = core.settle(CFG, DEP, OK); forfeited = 140000 - 30000
    assert t["fee"] == forfeited // 10 and t["donate_or_remainder"] == forfeited - t["fee"] and t["bonus"] == 0


def test_bonus_pool_goes_to_winners_only():
    rows, t = core.settle(dict(CFG, forfeit_use="bonus_pool"), DEP, OK)
    assert [r["user"] for r in rows if r["bonus"]] == ["runner_a"] and t["bonus"] == (110000 - 11000)


def test_partial_refund_floor():
    rows, _ = core.settle(dict(CFG, partial_refund=True), DEP, OK); d = {r["user"]: r for r in rows}
    assert d["runner_d"]["refund"] == 50000 * 2 // 4 and d["runner_b"]["refund"] == 30000 * 1 // 4


def test_bad_config_and_participants(tmp_path):
    p = tmp_path / "c.json"
    for patch, msg in (({"goal_count": 0}, "goal_count"), ({"fee_rate": 2}, "fee_rate"), ({"forfeit_use": "x"}, "forfeit_use"), ({"end": "2026-10-01"}, "종료일")):
        p.write_text(json.dumps(dict(json.load(open(os.path.join(S, "config.json"))), **patch)), encoding="utf-8")
        with pytest.raises(ValueError, match=msg): core.load_config(str(p))
    q = tmp_path / "p.csv"; q.write_text("user,deposit\na,0\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_participants(str(q))
    q.write_text("user,deposit\na,100\na,100\n", encoding="utf-8")
    with pytest.raises(ValueError): core.read_participants(str(q))


def test_cli(capsys):
    a = [os.path.join(S, "config.json"), os.path.join(S, "participants.csv"), os.path.join(S, "logs.csv"), "--today", "2026-11-12"]
    assert main(a) == 0
    o = capsys.readouterr().out; assert "runner_a: 인증 4/4회 달성 → 환급 30,000원" in o and "송금하지 않습니다" in o and "사행성" in o
    assert main(["없음.json"] + a[1:]) == 2
