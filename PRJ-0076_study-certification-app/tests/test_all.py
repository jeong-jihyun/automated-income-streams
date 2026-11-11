import datetime as dt, os
import pytest
from studycert import core
from studycert.cli import main

CSV = os.path.join(os.path.dirname(__file__), "..", "sample", "logs.csv"); T = dt.date(2026, 11, 11)


def load():
    ok, bad = core.read(CSV, T); good, rej = core.validate(ok); return good, bad, rej


def test_read_filters_bad_rows():
    ok, bad = core.read(CSV, T); reasons = {r for _, _, r in bad}
    assert "미래 날짜" in reasons and "날짜/시간 형식 오류" in reasons and len(ok) == 11


def test_overlap_rejected():
    good, bad, rej = load(); assert (10, "park", "시간이 겹침") in [(r, m, w) for r, m, w in rej] or any(w == "시간이 겹침" and m == "park" for _, m, w in rej)
    assert sum(l["min"] for l in good if l["member"] == "park") == 180 + 0


def test_over_16h_rejected():
    good, bad, rej = load(); assert any(m == "choi" and w == "하루 16시간 초과" for _, m, w in rej)
    assert sum(l["min"] for l in good if l["member"] == "choi") == 600


def test_streak():
    good, *_ = load(); d = lambda m: [l["date"] for l in good if l["member"] == m]
    assert core.streak(d("kim"), T) == 3 and core.streak(d("lee"), T) == 4
    assert core.streak([dt.date(2026, 11, 10)], T) == 1 and core.streak([dt.date(2026, 11, 8)], T) == 0 and core.streak([], T) == 0


def test_ranking_and_ties():
    good, *_ = load(); rk = core.ranking(good, dt.date(2026, 11, 5), T)
    assert [r["member"] for r in rk][0] == "choi" and rk[0]["min"] == 600
    logs = [{"member": "a", "date": T, "min": 60}, {"member": "b", "date": T, "min": 60}, {"member": "c", "date": T, "min": 30}]
    r = core.ranking(logs, T, T); assert [x["rank"] for x in r] == [1, 1, 3]


def test_ranking_period_filter():
    good, *_ = load(); rk = core.ranking(good, T, T); assert {r["member"] for r in rk} == {"kim", "lee"}


def test_flags_repeated_duration():
    good, *_ = load(); assert core.flags(good, repeat=4) == [("lee", 60, 4)] and core.flags(good, repeat=5) == []


def test_report_text():
    good, bad, rej = load(); t = core.report(good, bad, rej, T, dt.date(2026, 11, 5), T)
    assert "1위 choi" in t and "[제외]" in t and "[확인] lee: 60분 기록이 4번 반복됨 (부정 확정 아님)" in t and "실제 공부 여부는 확인하지 않습니다" in t


def test_hm():
    assert core.hm(125) == "2시간 5분"


def test_missing_columns(tmp_path):
    p = tmp_path / "x.csv"; p.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="필수 열"): core.read(str(p), T)


def test_cli(capsys):
    assert main([CSV, "--today", "2026-11-11", "--since", "2026-11-05"]) == 0
    assert "1위 choi" in capsys.readouterr().out and main(["없음.csv"]) == 2
