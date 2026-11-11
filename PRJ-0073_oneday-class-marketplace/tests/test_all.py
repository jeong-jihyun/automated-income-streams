import datetime as dt, json, os
import pytest
from classmkt import core
from classmkt.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); CL = core.load_classes(os.path.join(S, "classes.json"))
ST, LOG, ERR = core.process(CL, os.path.join(S, "bookings.csv")); E = {(w, m) for _, w, m in ERR}


def test_capacity_and_waitlist_promotion():
    # C1 정원 2: kim, lee 확정 → park 대기 → lee 취소(14일 전) 때 park 승격 → 11/18 kim 취소로 park만 남음
    assert ST["C1"]["confirmed"] == ["park"] and ST["C1"]["wait"] == []
    assert ("park", "대기→확정") in [(w, a) for _, c, w, a in LOG if c == "C1"]


def test_never_over_capacity_or_duplicate():
    for cid, s in ST.items():
        assert len(s["confirmed"]) <= CL[cid]["capacity"] and len(set(s["confirmed"] + s["wait"])) == len(s["confirmed"] + s["wait"])


def test_refund_policy_ratios():
    assert [core.refund_ratio(d) for d in (10, 7, 5, 3, 2, 1, 0.5)] == [1.0, 1.0, 0.5, 0.5, 0.3, 0.3, 0.0]


def test_refund_amounts():
    # lee: 수업 14일 전 취소 → 40,000 전액 / kim: 2.2일 전 취소 → 30% = 12,000 / 결제는 kim·lee·승격한 park 3명분
    assert ST["C1"]["refunded"] == 40000 + 12000 and ST["C1"]["paid"] == 40000 * 3


def test_errors_collected():
    assert ("kim", "이미 신청함") in E and ("han", "이미 시작한 수업") in E and ("x", "없는 클래스") in E
    assert ("ghost", "취소할 신청이 없음") in E and ("yoon", "알 수 없는 action 'refund'") in E


def test_settlement_conserves_money():
    rows, inst = core.settle(CL, ST)
    for r in rows: assert r["paid"] - r["refunded"] == r["fee"] + r["pay"]
    assert sum(v["pay"] + v["fee"] for v in inst.values()) == sum(r["paid"] - r["refunded"] for r in rows)


def test_min_students_closes_class():
    rows, _ = core.settle(CL, ST, cancel_check=dt.datetime(2026, 11, 13)); d = {r["id"]: r for r in rows}
    assert d["C3"]["closed"] and d["C3"]["pay"] == 0 and d["C3"]["refunded"] == d["C3"]["paid"] == 60000
    assert d["C1"]["closed"] and not d["C2"]["closed"]          # C1: 1명(최소 2), C2: 최소 1명 충족


def test_no_cancel_check_means_no_closure():
    assert not any(r["closed"] for r in core.settle(CL, ST)[0])


def test_bad_classes(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([{"id": "a", "title": "t", "instructor": "i", "price": 1, "capacity": 0, "start": "2026-01-01T10:00"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="값 오류"): core.load_classes(str(p))
    p.write_text(json.dumps([{"id": "a"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="title"): core.load_classes(str(p))
    b = tmp_path / "b.csv"; b.write_text("time,class_id,student,action\nlater,C1,a,book\n", encoding="utf-8")
    with pytest.raises(ValueError, match="time"): core.process(CL, str(b))


def test_cli(capsys):
    a = [os.path.join(S, "classes.json"), os.path.join(S, "bookings.csv")]
    assert main(a + ["--now", "2026-11-13T00:00"]) == 0
    o = capsys.readouterr().out; assert "폐강 후보" in o and "강사 공방A" in o and "송금은 하지 않으며" in o
    assert main(a + ["--commission", "1.5"]) == 2 and main(["없음.json", a[1]]) == 2
