import os
import pytest
from seniorlearn import core
from seniorlearn.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample")
L, C, A = (os.path.join(D, f) for f in ("learners.csv", "classes.csv", "attend.csv"))


def setup():
    ls, bl = core.read_learners(L); cs, bc = core.read_classes(C); return ls, bl, cs, bc


def test_bad_rows_excluded():
    ls, bl, cs, bc = setup(); assert len(ls) == 5 and bl == [(6, "level은 1~3")] and bc == []


def test_phone_masked():
    assert core.mask_phone("010-1234-5678") == "010-****-5678" and core.mask_phone("") == "(번호 없음)"


def test_capacity_and_waitlist():
    ls, _, cs, _ = setup(); seats, wait, none = core.enroll(ls, cs)
    assert len(seats["C1"]) <= 2 and all(len(seats[c["id"]]) <= c["cap"] for c in cs)
    assert set(seats["C1"]) | set(wait["C1"]) >= {"김순자", "이말순"}


def test_challenge_class_one_level_up_only():
    ls, _, cs, _ = setup()
    assert core.fits(ls[0], cs[1]) is True       # 김순자 level1, C2 level2 → 도전 가능
    assert core.fits(ls[0], cs[3]) is False      # C4 level3 은 두 단계 위, 주제·요일도 다름


def test_no_class_listed():
    ls, _, cs, _ = setup(); *_, none = core.enroll(ls, cs); assert none == ["한복순"]
    assert "최철수" not in none


def test_notice_large_text_lines():
    ls, _, cs, _ = setup(); t = core.notice(cs[0], ["김순자"], ["이말순"])
    assert "요일: 화요일" in t and "수준: 기초" in t and "대기: 이말순" in t and "010" not in t


def test_attendance_streak_flag():
    r = {x["name"]: x for x in core.attendance(A)}
    assert r["김순자"]["reach"] is True and r["김순자"]["rate"] == 33 and r["이말순"]["reach"] is False


def test_missing_column(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("name\nx\n", encoding="utf-8")
    with pytest.raises(ValueError):
        core.read_learners(str(p))


def test_cli(capsys):
    assert main(["enroll", L, C]) == 0 and "수업 ]" in capsys.readouterr().out
    assert main(["attend", A]) == 0 and "연락 권유" in capsys.readouterr().out
    assert main(["attend", "nope.csv"]) == 2
