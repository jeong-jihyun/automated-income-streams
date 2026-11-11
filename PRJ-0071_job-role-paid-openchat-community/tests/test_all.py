import datetime as dt, os
import pytest
from jobchat import core
from jobchat.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample"); F = os.path.join(S, "members.csv"); T = dt.date(2026, 11, 11)
MS = core.read_members(F)


def test_status():
    s = {m["id"]: core.status(m, T) for m in MS}
    assert s["dev_a"] == "이용 중" and s["dev_b"] == "곧 만료" and s["pm_a"] == "만료"


def test_reminders_only_for_soon_and_expired():
    r = dict(core.reminders(MS, T)); assert set(r) == {"dev_b", "pm_a"} and "4일 뒤" in r["dev_b"] and "제외됩니다" in r["pm_a"]


def test_match_senior_interviews_junior_with_common_slot():
    pairs, _ = core.match(MS, T)
    p = [x for x in pairs if x["role"] == "백엔드"][0]
    assert (p["interviewer"], p["candidate"], p["slot"]) == ("dev_a", "dev_b", "화20")


def test_expired_excluded_from_matching():
    pairs, left = core.match(MS, T); assert all("pm_a" not in (x["interviewer"], x["candidate"]) for x in pairs)
    d = dict(left); assert d["pm_a"] == "이용 기간 만료"


def test_no_slot_overlap_and_lonely_reasons():
    _, left = core.match(MS, T)
    d = dict(left); assert d["dev_c"] == "겹치는 시간대가 있는 상대가 없음" and d["ds_a"] == "같은 직무에 다른 회원이 없음" and d["pm_b"] == "같은 직무에 다른 회원이 없음"


def test_each_member_once():
    pairs, _ = core.match(MS, T); ids = [i for p in pairs for i in (p["interviewer"], p["candidate"])]
    assert len(ids) == len(set(ids))


def test_post_rules():
    assert core.check_post("카톡ID 알려드려요 010-1234-5678") == ["연락처 공개"]
    assert "외부 결제·입금 유도" in core.check_post("계좌번호 보내드릴게요")
    assert "수익·합격 보장 표현" in core.check_post("100% 합격 보장") and core.check_post("면접 질문 공유합니다") == []


def test_bad_members_file(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("member_id,role,level,paid_until,slots\na,x,신입,2026-01-01,월\n", encoding="utf-8")
    with pytest.raises(ValueError, match="level"): core.read_members(str(p))
    p.write_text("member_id,role,level,paid_until,slots\na,x,주니어,2026-01-01,월\na,x,주니어,2026-01-01,월\n", encoding="utf-8")
    with pytest.raises(ValueError, match="중복"): core.read_members(str(p))
    p.write_text("member_id,role,level,paid_until,slots\na,x,주니어,내일,월\n", encoding="utf-8")
    with pytest.raises(ValueError, match="paid_until"): core.read_members(str(p))
    p.write_text("member_id,role\n", encoding="utf-8")
    with pytest.raises(ValueError, match="필수 열"): core.read_members(str(p))


def test_cli(capsys):
    assert main(["report", F, "--today", "2026-11-11"]) == 0
    o = capsys.readouterr().out; assert "곧 만료: 1명" in o and "면접관 dev_a ↔ 지원자 dev_b" in o and "보내지 않습니다" in o
    assert main(["remind", F, "--today", "2026-11-11"]) == 0 and "4일 뒤" in capsys.readouterr().out
    assert main(["check", "입금 부탁드려요"]) == 0 and "입금 유도" in capsys.readouterr().out
    assert main(["report", "없음.csv"]) == 2
