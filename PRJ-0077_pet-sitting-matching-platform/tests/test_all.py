import datetime as dt, os
import pytest
from petsit import core
from petsit.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample")
RQ, ST = os.path.join(D, "requests.csv"), os.path.join(D, "sitters.csv")


def run():
    rq, bq = core.read_requests(RQ); st, bs = core.read_sitters(ST)
    done, left = core.match(rq, st); return rq, bq, st, bs, done, left


def test_bad_request_row_excluded():
    rq, bq, *_ = run(); assert len(rq) == 6 and bq == [(8, "끝 날짜가 시작보다 빠름")]


def test_region_and_pet_mismatch_unassigned():
    *_, left = run(); why = dict((r["id"], w) for r, w in left)
    assert why["R5"] == "지역 불일치"


def test_large_dog_goes_to_nobody_when_over_max_size():
    *_, left = run(); assert "R2" in [r["id"] for r, _ in left]
    assert dict((r["id"], w) for r, w in left)["R2"] == "크기 초과"


def test_capacity_respected():
    _, _, st, _, done, _ = run()
    by = {}
    for r, n in done:
        by.setdefault(n, []).append(r)
    for s in st:
        mine = by.get(s["name"], [])
        for r in mine:
            assert sum(1 for x in mine if core.overlap(x, r)) <= s["capacity"]


def test_period_outside_availability():
    sit = {"name": "x", "regions": {"마포"}, "pets": {"dog"}, "max_size": "small", "capacity": 1,
           "from": dt.date(2026, 12, 1), "to": dt.date(2026, 12, 5)}
    req = {"id": "q", "owner": "o", "region": "마포", "pet": "dog", "size": "small", "start": dt.date(2026, 12, 4), "end": dt.date(2026, 12, 8)}
    assert core.why_not(req, sit, []) == "가능 기간 밖"


def test_all_matched_requests_satisfy_rules():
    _, _, st, _, done, _ = run(); by = {s["name"]: s for s in st}
    for r, n in done:
        assert core.why_not(r, by[n], []) is None


def test_deterministic():
    assert run()[4] == run()[4]


def test_missing_column(tmp_path):
    p = tmp_path / "a.csv"; p.write_text("id,owner\n1,a\n", encoding="utf-8")
    with pytest.raises(ValueError):
        core.read_requests(str(p))


def test_duplicate_id(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("id,owner,region,pet,size,start,end\n1,a,x,dog,small,2026-01-01,2026-01-02\n1,b,x,dog,small,2026-01-01,2026-01-02\n", encoding="utf-8")
    ok, bad = core.read_requests(str(p)); assert len(ok) == 1 and bad[0][1].startswith("번호")


def test_report_has_disclaimer_and_exclusions():
    rq, bq, st, bs, done, left = run(); t = core.report(done, left, bq, bs)
    assert "결제는 이 도구가 하지 않습니다" not in t and "연락·결제·후기는 이 도구가 하지 않습니다" in t and "[제외] 요청 8행" in t


def test_cli(capsys):
    assert main([RQ, ST]) == 0 and "배정" in capsys.readouterr().out
    assert main(["nope.csv", ST]) == 2
