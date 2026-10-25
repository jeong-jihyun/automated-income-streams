import csv
import json
import os
import pytest
from snsgen import generate as G, store, templates as T
from snsgen.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "shop.json")
SHOP = store.load(S)


def test_store_validation(tmp_path):
    p = tmp_path / "s.json"
    for bad, msg in (({}, "name"), ({"name": "a", "category": "x", "location": "b", "items": ["c"]}, "category"), ({"name": "a", "category": "cafe", "location": "b", "items": ["c"], "tone": "rude"}, "tone")):
        p.write_text(json.dumps(bad)); 
        with pytest.raises(store.SnsError, match=msg): store.load(str(p))
    p.write_text("{"); 
    with pytest.raises(store.SnsError, match="JSON"): store.load(str(p))


def test_no_consecutive_same_theme_and_reproducible():
    a = G.generate(SHOP, "2026-11-01", 30, 5); b = G.generate(SHOP, "2026-11-01", 30, 5)
    assert a == b and all(a[i]["theme"] != a[i + 1]["theme"] for i in range(29)) and a[0]["date"] == "2026-11-01" and a[-1]["date"] == "2026-11-30"
    assert G.generate(SHOP, "2026-11-01", 30, 6) != a


def test_variety_and_repeat_flag():
    posts = G.generate(SHOP, "2026-11-01", 30, 1); caps = [p["caption"] for p in posts]
    assert len(set(caps)) >= 28 and sum(p["repeat"] for p in posts) == 30 - len(set(caps))
    one = G.generate(dict(SHOP, items=["라떼"], promos=[], hours=""), "2026-11-01", 60, 1)
    assert any(p["repeat"] for p in one)                                   # 재료가 모자라면 반복을 숨기지 않고 표시


def test_korean_particles():
    assert G.fmt("{item|을/를}", item="레몬에이드") == "레몬에이드를" and G.fmt("{item|을/를}", item="크로플") == "크로플을"
    assert G.fmt("{name|이/가}", name="해든 카페") == "해든 카페가" and G.fmt("{name|이/가}", name="책방") == "책방이"
    assert G.fmt("{item|으로/로}", item="커피") == "커피로" and G.fmt("{item|으로/로}", item="빵") == "빵으로" and G.fmt("{item|으로/로}", item="물") == "물로"
    assert G.fmt("{name|이에요/예요}", name="해든 카페") == "해든 카페예요" and G.fmt("{name|이에요/예요}", name="책방") == "책방이에요"
    assert G.fmt("{name|은/는}", name="ABC") == "ABC는"
    import re
    for p in G.generate(SHOP, "2026-11-01", 62, 9): assert not re.search(r"[가-힣](을를|이가|은는)", p["caption"]) and "{" not in p["caption"]


def test_only_given_facts_used():
    no_promo = dict(SHOP, promos=[], hours="")
    posts = G.generate(no_promo, "2026-11-01", 40, 2)
    assert all(p["theme"] not in ("이벤트", "영업시간 안내") for p in posts)
    assert all("할인" not in p["caption"] and "%" not in p["caption"] for p in G.generate(SHOP, "2026-11-01", 40, 3))


def test_tone_formal():
    posts = G.generate(dict(SHOP, tone="formal"), "2026-11-01", 20, 1)
    assert not any("😊" in p["caption"] or "🎉" in p["caption"] for p in posts)


def test_banned_phrases_flagged():
    assert G.check("우리가 최고예요")[0].startswith("과장") and G.check("100% 효과") and G.check("평범한 글") == [] and G.check("가" * 2300)
    bad = dict(SHOP, items=["국내 유일 레몬에이드"])
    assert any(p["problems"] for p in G.generate(bad, "2026-11-01", 20, 1))


def test_tags_limit_and_ad_label():
    many = dict(SHOP, extra_tags=[f"t{i}" for i in range(30)])
    t = G.tags(many); assert len(t) == G.MAX_TAGS and len(set(t)) == len(t) and all(x.startswith("#") for x in t)
    ad = G.tags(dict(many, sponsored=True)); assert "#광고" in ad and len(ad) == G.MAX_TAGS
    assert "#광고" not in G.tags(SHOP)


def test_days_range_and_cli(tmp_path, capsys):
    with pytest.raises(ValueError): G.generate(SHOP, "2026-11-01", 0)
    out = str(tmp_path / "c.csv")
    assert main([S, "--start", "2026-11-01", "--days", "7", "--out", out]) == 0
    rows = list(csv.reader(open(out, encoding="utf-8-sig"))); assert rows[0][0] == "날짜" and len(rows) == 8
    assert main([str(tmp_path / "no.json"), "--start", "2026-11-01", "--out", out]) == 2 and main([S, "--start", "bad", "--out", out]) == 2
