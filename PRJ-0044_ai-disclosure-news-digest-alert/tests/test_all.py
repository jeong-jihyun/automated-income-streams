import json, os
import pytest
from digest import core, rules
from digest.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "items.json")
ITEMS = core.load_items(S)


def test_classify():
    assert rules.classify("가나 유상증자 결정") == ("유상증자·감자", 3) and rules.classify("A 임원 변경") == ("임원·지분", 1)
    assert rules.classify("오늘의 날씨") == ("기타", 1)
    assert rules.classify("배당 및 유상증자") == ("유상증자·감자", 3)               # 높은 등급 우선


def test_similar_and_dedupe():
    assert core.similar("가나전자 유상증자 결정", "가나전자, 유상증자 결정") and not core.similar("유상증자 결정", "영업이익 잠정실적")
    recs, skip = core.build(ITEMS, ["가나전자"])
    assert len(recs) == 2 and skip["duplicate"] == 1 and recs[0]["also"] == ["뉴스A(예시)"]


def test_sort_by_importance_then_time():
    recs, _ = core.build(ITEMS, ["가나전자", "다라화학", "마바식품"])
    assert [r["importance"] for r in recs] == [3, 2, 2, 1] and recs[1]["time"] <= recs[2]["time"]


def test_watch_filter_and_empty_watch():
    recs, skip = core.build(ITEMS, ["다라화학"]); assert [r["id"] for r in recs] == ["d3"] and skip["not_watched"] == 4
    assert len(core.build(ITEMS, [])[0]) == 4


def test_min_importance():
    recs, skip = core.build(ITEMS, [], min_importance=3); assert len(recs) == 1 and skip["low"] == 3


def test_validation(tmp_path):
    p = tmp_path / "x.json"; p.write_text(json.dumps([{"id": "1", "title": "t", "time": "t"}]))
    with pytest.raises(core.DigestError, match="source"): core.load_items(str(p))
    p.write_text("{}"); 
    with pytest.raises(core.DigestError): core.load_items(str(p))
    with pytest.raises(core.DigestError): core.load_items(str(tmp_path / "none.json"))


def test_render_has_source_time_disclaimer():
    recs, _ = core.build(ITEMS, ["가나전자"]); t = core.render(recs)
    assert "출처: 공시(예시)" in t and "2026-10-26T09:00" in t and "원문: https://example.com/d2" in t and "투자 자문이 아니며" in t and "같은 내용 1건 더" in t
    assert "새로 알릴 항목이 없습니다" in core.render([])
    assert "매수" not in t.replace("매수·매도 권유나", "")                             # 추천 문구 없음


def test_state_prevents_repeat(tmp_path):
    st, sent = str(tmp_path / "s.json"), []
    r1 = core.run(ITEMS, ["가나전자"], st, sent.append); r2 = core.run(ITEMS, ["가나전자"], st, sent.append)
    assert len(sent) == 1 and len(r1[0]) == 2 and r1[2] is True
    assert r2[0] == [] and r2[2] is False and r2[1]["already_sent"] == 3          # 합쳐진 중복 기사(n1)도 다시 알리지 않음


def test_failed_send_not_recorded(tmp_path):
    st = str(tmp_path / "s.json")
    def boom(_): raise RuntimeError("전송 실패")
    with pytest.raises(RuntimeError): core.run(ITEMS, [], st, boom)
    assert core.load_state(st) == set()                                              # 실패하면 기록 안 함 → 다음에 재시도
    got = []; core.run(ITEMS, [], st, got.append); assert len(got) == 1


def test_dry_run_and_cli(tmp_path, capsys):
    st = str(tmp_path / "s.json")
    assert main([S, "--watch", "가나전자", "--state", st, "--dry-run"]) == 0 and not os.path.exists(st)
    assert "건너뜀" in capsys.readouterr().out
    assert main([S, "--state", st]) == 0 and len(core.load_state(st)) == 5
    assert main([str(tmp_path / "none.json")]) == 2
