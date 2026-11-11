import datetime as dt, json, os
import pytest
from fxalert import core
from fxalert.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
RULES = core.load_rules(os.path.join(S, "rules.json")); RD, BAD = core.load_readings(os.path.join(S, "readings.csv"))


def test_reads_and_skips_bad_line():
    assert len(RD) == 8 and BAD == 1 and RD == sorted(RD)


def test_alert_only_on_crossing():
    al, _, _ = core.evaluate(RULES, RD)
    usd = [a for a in al if a["rule"] == "usd-high"]
    assert [a["price"] for a in usd] == [1401.5] and "1,401.50 >= 1,400.00" in usd[0]["text"]


def test_low_rule_triggers():
    al, _, _ = core.evaluate(RULES, RD); assert [a["price"] for a in al if a["rule"] == "jpy-low"] == [8.95]


def test_spike_skipped_and_noted():
    al, _, notes = core.evaluate(RULES, RD); assert all(a["price"] != 2900.0 for a in al) and any("의심 값" in n for n in notes)


def test_rearm_after_leaving_threshold():
    # 1398(기준보다 0.14% 아래, 재장전 폭 0.2% 미만) -> 재장전 안 됨, 12:00 1402는 알림 없음
    al, st, _ = core.evaluate(RULES, RD); assert len([a for a in al if a["rule"] == "usd-high"]) == 1 and st["usd-high"]["armed"] is False
    rd = [(dt.datetime(2026, 11, 11, h), "USD/KRW", p) for h, p in ((9, 1401), (10, 1390), (12, 1402))]
    al2, _, _ = core.evaluate([dict(RULES[0], cooldown_min=30)], rd); assert [a["price"] for a in al2] == [1401, 1402]


def test_cooldown_blocks_even_when_rearmed():
    rd = [(dt.datetime(2026, 11, 11, 9, m), "USD/KRW", p) for m, p in ((0, 1401), (10, 1390), (20, 1402))]
    al, _, _ = core.evaluate([dict(RULES[0], cooldown_min=60)], rd); assert len(al) == 1


def test_state_persists_between_runs(tmp_path):
    al, st, _ = core.evaluate(RULES, RD); p = str(tmp_path / "s.json"); core.save_state(p, st)
    al2, _, _ = core.evaluate(RULES, RD, core.load_state(p)); assert al2 == []        # 이미 처리한 가격은 다시 보지 않음(재실행해도 중복 알림 없음)
    rd2 = RD + [(dt.datetime(2026, 11, 12, 9), "USD/KRW", 1390.0), (dt.datetime(2026, 11, 12, 10), "USD/KRW", 1405.0)]
    al3, _, _ = core.evaluate(RULES, rd2, core.load_state(p)); assert [a['price'] for a in al3] == [1405.0]      # 새 가격만 평가
    assert os.listdir(tmp_path) == ["s.json"]


def test_stale_warning():
    _, _, n = core.evaluate(RULES, RD, now=dt.datetime(2026, 11, 11, 20, 0)); assert any("오래됨" in x for x in n)
    _, _, n2 = core.evaluate(RULES, RD, now=dt.datetime(2026, 11, 11, 12, 30)); assert not any("오래됨" in x for x in n2)


def test_bad_rules(tmp_path):
    p = tmp_path / "r.json"
    for bad, msg in (([{"id": "a", "pair": "X", "op": "=", "threshold": 1}], "op"), ([{"id": "a", "pair": "X", "op": ">=", "threshold": -1}], "기준값"),
                     ([{"id": "a", "pair": "X"}], "op"), ([{"id": "a", "pair": "X", "op": ">=", "threshold": 1}] * 2, "중복"), ([{"id": "_seen", "pair": "X", "op": ">=", "threshold": 1}], "_로 시작")):
        p.write_text(json.dumps(bad), encoding="utf-8")
        with pytest.raises(ValueError, match=msg): core.load_rules(str(p))


def test_cli_outbox_and_state(tmp_path, capsys):
    a = [os.path.join(S, "rules.json"), os.path.join(S, "readings.csv"), "--state", str(tmp_path / "s.json"), "--outbox", str(tmp_path / "o.jsonl")]
    assert main(a) == 0
    o = capsys.readouterr().out; assert "기준가 도달" in o and "보내지 않습니다" in o and "읽지 못한 가격 1줄" in o
    assert len(open(tmp_path / "o.jsonl", encoding="utf-8").read().splitlines()) == 2
    assert main(a) == 0 and "새로 알릴 것이 없습니다" in capsys.readouterr().out
    assert main(["없음.json", a[1]]) == 2
