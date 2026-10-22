import os
from datetime import datetime
import pytest
from noshow import core
from noshow.cli import main

CFG = core.load_config(os.path.join(os.path.dirname(__file__), "..", "sample", "config.json"))
D = lambda s: datetime.strptime(s, core.FMT)


class Out:
    def __init__(self): self.msgs = []
    def __call__(self, phone, text): self.msgs.append((phone, text))


@pytest.fixture
def db(): return core.connect()


def test_add_validation(db):
    core.add(db, "가", "010-1234-5678", "2031-03-05 10:00")
    for args, msg in [(("가", "010-1234-5678", "2031-03-05 10:00"), "이미 예약"), (("", "010-1234-5678", "2031-03-05 11:00"), "이름"),
                      (("가", "02-123-4567", "2031-03-05 11:00"), "휴대폰"), (("가", "010-1234-5678", "3/5 11시"), "형식")]:
        with pytest.raises(core.NoshowError, match=msg): core.add(db, *args)


def test_reminders_once_per_point(db):
    core.add(db, "가", "010-1234-5678", "2031-03-05 10:00")
    s = Out()
    assert core.send_due(db, CFG, D("2031-03-03 09:00"), s) == 0                 # 아직 이름
    assert core.send_due(db, CFG, D("2031-03-04 10:00"), s) == 1 and "03월 05일 10:00" in s.msgs[0][1]   # 24시간 전
    assert core.send_due(db, CFG, D("2031-03-04 11:00"), s) == 0                 # 같은 시점 중복 없음
    assert core.send_due(db, CFG, D("2031-03-05 08:00"), s) == 1                 # 2시간 전
    assert core.send_due(db, CFG, D("2031-03-05 08:30"), s) == 0 and core.send_due(db, CFG, D("2031-03-05 10:30"), s) == 0   # 지난 예약은 안 보냄


def test_failed_send_retried(db):
    core.add(db, "가", "010-1234-5678", "2031-03-05 10:00")
    def boom(*a): raise ConnectionError("x")
    assert core.send_due(db, CFG, D("2031-03-04 10:00"), boom) == 0
    assert core.send_due(db, CFG, D("2031-03-04 10:05"), Out()) == 1


def test_confirmed_only_gets_last_reminder(db):
    core.add(db, "가", "010-1234-5678", "2031-03-05 10:00")
    assert core.handle_reply(db, CFG, "010-1234-5678", "1", D("2031-03-04 09:00"), Out()) == "confirmed"
    s = Out(); assert core.send_due(db, CFG, D("2031-03-04 10:00"), s) == 0
    assert core.send_due(db, CFG, D("2031-03-05 08:00"), s) == 1


def test_cancel_offers_slot_to_first_waiter_then_next_on_decline_or_timeout(db):
    s = Out()
    core.add(db, "가", "010-1111-1111", "2031-03-05 10:00")
    core.join_waitlist(db, "나", "010-2222-2222", "2031-03-05 10:00"); core.join_waitlist(db, "다", "010-3333-3333", "2031-03-05 10:00")
    now = D("2031-03-04 09:00")
    assert core.handle_reply(db, CFG, "010-1111-1111", "2", now, s) == "cancelled"
    assert s.msgs[-1][0] == "010-2222-2222" and "15분" in s.msgs[-1][1]
    assert core.handle_reply(db, CFG, "010-2222-2222", "아니오", now, s) == "offer_declined"
    assert s.msgs[-1][0] == "010-3333-3333"                                      # 다음 대기자
    assert core.expire_offers(db, CFG, D("2031-03-04 09:10"), s) == 0
    assert core.expire_offers(db, CFG, D("2031-03-04 09:16"), s) == 1             # 시간 초과 → 대기자 없음
    # 새 시간대: 수락 흐름
    core.add(db, "라", "010-4444-4444", "2031-03-06 10:00"); core.join_waitlist(db, "마", "010-5555-5555", "2031-03-06 10:00")
    core.handle_reply(db, CFG, "010-4444-4444", "취소", now, s)
    assert core.handle_reply(db, CFG, "010-5555-5555", "네", now, s) == "offer_accepted"
    assert db.execute("SELECT status FROM appts WHERE phone='010-5555-5555'").fetchone()[0] == "confirmed"
    with pytest.raises(core.NoshowError): core.add(db, "바", "010-6666-6666", "2031-03-06 10:00")   # 슬롯 중복 불가


def test_unknown_reply_and_noshow_stats(db):
    core.add(db, "가", "010-1234-5678", "2031-03-05 10:00")
    assert core.handle_reply(db, CFG, "010-1234-5678", "음...", D("2031-03-04 09:00"), Out()) is None
    assert core.handle_reply(db, CFG, "010-9999-9999", "1", D("2031-03-04 09:00"), Out()) is None
    core.add(db, "가", "010-1234-5678", "2031-03-07 10:00"); core.handle_reply(db, CFG, "010-1234-5678", "1", D("2031-03-04 09:00"), Out())
    assert core.mark_noshows(db, D("2031-03-05 11:00")) == 1            # 3/5 미확인 예약 → 노쇼, 3/7은 아직 미래
    assert core.noshow_rate(db, "010-1234-5678") == 100.0
    core.mark_done(db, 2)                                              # 3/7 예약 방문 완료
    with pytest.raises(core.NoshowError): core.mark_done(db, 2)
    assert core.noshow_rate(db, "010-1234-5678") == 50.0 and core.noshow_rate(db, "010-0000-0000") is None
    core.add(db, "나", "010-7777-7777", "2031-03-08 10:00"); core.handle_reply(db, CFG, "010-7777-7777", "1", D("2031-03-04 09:00"), Out())
    assert core.mark_noshows(db, D("2031-03-08 12:00")) == 1           # 확인했지만 오지 않은 손님도 노쇼로 집계


def test_config_errors(tmp_path):
    for t in ("{", '{"shop": "a"}', '{"shop":"a","template":"t","remind_hours_before":[0]}'):
        f = tmp_path / "c.json"; f.write_text(t)
        with pytest.raises(core.NoshowError): core.load_config(str(f))


def test_cli(tmp_path, capsys):
    cfg = os.path.join(os.path.dirname(__file__), "..", "sample", "config.json"); db = str(tmp_path / "n.db")
    assert main(["--db", db, "--config", cfg, "add", "가", "010-1234-5678", "2031-03-05 10:00"]) == 0
    assert main(["--db", db, "--config", cfg, "remind", "--now", "2031-03-04 10:00"]) == 0 and "문자 시험 출력" in capsys.readouterr().out
    assert main(["--db", db, "--config", cfg, "reply", "010-1234-5678", "1", "--now", "2031-03-04 11:00"]) == 0
    assert main(["--db", db, "--config", cfg, "add", "가", "bad", "2031-03-05 12:00"]) == 2
