import json
import os
import pytest
from tripplan import planner as T
from tripplan.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "places.json")
PL = json.load(open(S, encoding="utf-8"))


def all_items(r):
    return [i for d in r["days"] for i in d]


def test_budget_never_exceeded():
    for b in (0, 10000, 40000, 100000, 10**7):
        r = T.plan(PL, 3, b, ["food"]); assert r["spent"] <= b


def test_interests_prioritized_under_tight_budget():
    r = T.plan(PL, 1, 30000, ["craft"], "relaxed")
    assert "도자기 체험" in [i["place"]["name"] for i in all_items(r)]


def test_each_place_once_and_day_limits():
    r = T.plan(PL, 2, 10**6, [], "normal"); ids = [i["place"]["id"] for i in all_items(r)]
    assert len(ids) == len(set(ids)) and all(len(d) <= 4 for d in r["days"]) and len(r["days"]) == 2


def test_times_respect_opening_hours_and_order():
    r = T.plan(PL, 3, 10**6, [], "packed")
    for d in r["days"]:
        prev_end = 0
        for it in d:
            o, c = (T.hm(x) for x in it["place"]["open"].split("-"))
            assert it["start"] >= o and it["end"] <= c and it["start"] >= prev_end and it["end"] <= T.DAY_END
            prev_end = it["end"]


def test_late_opening_place_scheduled_late_or_dropped():
    only = [p for p in PL if p["id"] == "a5"]
    r = T.plan(only, 1, 10**6, [], "relaxed"); it = all_items(r)[0]
    assert it["start"] == T.hm("18:00")


def test_unschedulable_is_reported():
    p = dict(PL[0], id="z", open="09:00-09:30", minutes=60)
    r = T.plan([p], 1, 10**6); assert r["unscheduled"] == [p["name"]] and r["spent"] == 0


def test_distance_function():
    assert T.km({"lat": 0, "lon": 0}, {"lat": 0, "lon": 1}) == pytest.approx(111.19, abs=0.1)
    assert T.km(PL[0], PL[0]) == 0


def test_validation_errors():
    with pytest.raises(T.PlanError, match="비었"): T.plan([], 1, 1)
    with pytest.raises(T.PlanError, match="일수"): T.plan(PL, 0, 1)
    with pytest.raises(T.PlanError, match="예산"): T.plan(PL, 1, -1)
    with pytest.raises(T.PlanError, match="속도"): T.plan(PL, 1, 1, pace="fast")
    with pytest.raises(T.PlanError, match="중복"): T.plan(PL + [PL[0]], 1, 1)
    with pytest.raises(T.PlanError, match="형식"): T.plan([dict(PL[0], open="9-18")], 1, 1)
    with pytest.raises(T.PlanError, match="정보 부족"): T.plan([{"id": "x"}], 1, 1)


def test_render_discloses_affiliate_and_budget():
    r = T.plan(PL, 3, 200000, ["craft"]); md = T.render(r, 200000)
    assert "제휴 링크" in md and "예산 200,000원" in md and "공식 안내" in md
    r2 = T.plan([p for p in PL if "link" not in p], 1, 10**6); assert "제휴 링크" not in T.render(r2, 10**6)


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "t.md")
    assert main([S, "--days", "2", "--budget", "100000", "--interests", "food,nature", "--out", out]) == 0 and "1일차" in open(out, encoding="utf-8").read()
    assert main([S, "--days", "0", "--budget", "1"]) == 2 and main(["nofile.json", "--days", "1", "--budget", "1"]) == 2
