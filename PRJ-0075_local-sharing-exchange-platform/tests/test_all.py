import datetime as dt, os
import pytest
from sharing import core
from sharing.cli import main

CSV = os.path.join(os.path.dirname(__file__), "..", "sample", "posts.csv"); T = dt.date(2026, 11, 11); P = {p["id"]: p for p in core.read(CSV)}


def test_read_all():
    assert len(P) == 7 and P["o1"]["lat"] == 37.500622


def test_prohibited_item_held():
    assert any("처방약" in w for w in core.check(P["o3"])) and core.check(P["o1"]) == []


def test_missing_dong_flagged():
    q = dict(P["o1"]); q["dong"] = ""; assert "동네(동) 정보 없음" in core.check(q)


def test_public_location_rounded():
    pl = core.public_location(P["o1"]); assert pl == {"dong": "역삼동", "lat": 37.5, "lon": 127.04} and "37.500622" not in str(pl)


def test_haversine():
    assert core.km({"lat": 37.5, "lon": 127.0}, {"lat": 37.5, "lon": 127.0}) == 0
    d = core.km({"lat": 37.5665, "lon": 126.9780}, {"lat": 35.1796, "lon": 129.0756}); assert 320 < d < 340   # 서울-부산


def test_expiry():
    assert [p["id"] for p in core.expired(core.read(CSV), T)] == ["w3"] and len(core.active(core.read(CSV), T)) == 6


def test_match_pairs_and_distance():
    res, held = core.match(core.read(CSV), T); d = {m["want"]: m for m in res}
    assert d["w1"]["offer"] == "o1" and d["w2"]["offer"] == "o2" and "w3" not in d and [h["id"] for h in held] == ["o3"]
    assert all(m["km"] <= 2.0 for m in res)


def test_far_offer_not_matched():
    posts = core.read(CSV); res, _ = core.match(posts, T, max_km=0.01); assert res == []


def test_offer_used_once():
    posts = core.read(CSV); w = dict(P["w1"]); w["id"] = "w9"; w["posted"] = dt.date(2026, 11, 10); posts.append(w)
    res, _ = core.match(posts, T); assert len([m for m in res if m["offer"] == "o1"]) == 1


def test_bad_inputs(tmp_path):
    p = tmp_path / "x.csv"
    p.write_text("id,kind,title,dong,lat,lon,posted\na,sell,t,d,1,1,2026-11-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="kind"): core.read(str(p))
    p.write_text("id,kind,title,dong,lat,lon,posted\na,offer,t,d,99,1,2026-11-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="범위"): core.read(str(p))
    p.write_text("id,kind,title,dong,lat,lon,posted\na,offer,t,d,1,1,2026-11-01\na,want,t,d,1,1,2026-11-01\n", encoding="utf-8")
    with pytest.raises(ValueError, match="중복"): core.read(str(p))
    p.write_text("a,b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="필수 열"): core.read(str(p))


def test_cli(capsys):
    assert main([CSV, "--today", "2026-11-11"]) == 0
    o = capsys.readouterr().out; assert "매칭 후보 2쌍" in o and "[보류] o3" in o and "[만료] w3" in o and "거래는 하지 않습니다" in o
    assert main(["없음.csv"]) == 2
