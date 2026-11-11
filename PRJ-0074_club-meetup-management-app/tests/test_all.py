import datetime as dt, os
import pytest
from clubapp import core
from clubapp.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); M = core.read_members(os.path.join(S, "members.csv")); PAY = os.path.join(S, "payments.csv"); EXP = os.path.join(S, "expenses.csv")


def test_dues_status_before_and_after_deadline():
    rows, unk = core.dues_status(M, PAY, "2026-11", dt.date(2026, 11, 8)); d = {r["member"]: r for r in rows}
    assert d["kim"]["status"] == "완납" and d["lee"]["status"] == "일부 납부" and d["lee"]["left"] == 4000 and d["park"]["status"] == "미납" and unk == ["outsider"]
    rows2, _ = core.dues_status(M, PAY, "2026-11", dt.date(2026, 11, 20)); d2 = {r["member"]: r for r in rows2}
    assert d2["park"]["status"] == "미납(기한 지남)" and d2["kim"]["status"] == "완납"


def test_other_month_payment_not_counted():
    rows, _ = core.dues_status(M, PAY, "2026-12", dt.date(2026, 12, 1)); assert all(r["paid"] == 0 for r in rows)


def test_split_keeps_total():
    s = core.split(100, ["a", "b", "c"]); assert sum(s.values()) == 100 and sorted(s.values()) == [33, 33, 34]


def test_balances_sum_to_zero():
    assert sum(core.balances(EXP).values()) == 0


def test_balances_values():
    b = core.balances(EXP)   # 50000/4=12500 / 23000/3=7667(kim),7667(lee),7666(park) / 100/3: 이름순 choi 34, kim 33, park 33
    assert b["kim"] == 50000 - 12500 - 7667 - 33 and b["choi"] == -12500 - 34


def test_transfers_settle_everyone():
    b = core.balances(EXP); t = core.transfers(b); after = dict(b)
    for f, to, amt in t: after[f] += amt; after[to] -= amt
    assert all(v == 0 for v in after.values()) and len(t) <= len(b) - 1


def test_transfers_empty_when_even():
    assert core.transfers({"a": 0, "b": 0}) == []


def test_rsvp_and_notice():
    ans = core.rsvp(os.path.join(S, "rsvp.csv"), "11-22"); assert ans == {"yes": ["kim"], "no": ["lee"], "maybe": ["park"]}
    n = core.notice("정기 모임", dt.datetime(2026, 11, 22, 14), "강남", dt.date(2026, 11, 11), ans, list(M))
    assert "D-11" in n and "참석 1명 / 불참 1명 / 미정 1명" in n and "아직 답이 없는 사람: choi" in n
    assert "오늘" in core.notice("x", dt.datetime(2026, 11, 11, 9), "y", dt.date(2026, 11, 11)) and "지남" in core.notice("x", dt.datetime(2026, 11, 1, 9), "y", dt.date(2026, 11, 11))


def test_bad_inputs(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("member,monthly_due\na,abc\n", encoding="utf-8")
    with pytest.raises(ValueError, match="정수"): core.read_members(str(p))
    p.write_text("member,monthly_due\na,1\na,1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="중복"): core.read_members(str(p))
    p.write_text("desc,payer,amount,participants\nx,a,0,a;b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="양수"): core.balances(str(p))
    p.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="필수 열"): core.balances(str(p))


def test_cli(capsys):
    assert main(["dues", os.path.join(S, "members.csv"), PAY, "--month", "2026-11", "--today", "2026-11-20"]) == 0
    o = capsys.readouterr().out; assert "park: 미납(기한 지남)" in o and "입금자: outsider" in o and "전송은 하지 않습니다" in o
    assert main(["settle", EXP]) == 0 and "송금" in capsys.readouterr().out
    assert main(["notice", "--title", "모임", "--when", "2026-11-22T14:00", "--place", "강남", "--rsvp", os.path.join(S, "rsvp.csv"), "--event", "11-22", "--members", os.path.join(S, "members.csv"), "--today", "2026-11-11"]) == 0
    assert "D-11" in capsys.readouterr().out
    assert main(["settle", "없음.csv"]) == 2
