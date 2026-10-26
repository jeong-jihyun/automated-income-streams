import os, json
from datetime import date
import pytest
from reviewblog import core
from reviewblog.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
V = core.load(os.path.join(S, "visit.json")); TODAY = date(2026, 10, 27)


def test_make_sponsor_top_bottom_and_dates():
    t = core.make(V, TODAY)
    assert t.startswith("※ 이 글은 업체로부터 음료 2잔을(를) 제공받아") and t.rstrip().endswith("솔직하게 썼습니다.") and "2026-10-24 방문" in t and "4,500원" in t and "2026-10-24 기준" in t and "아쉬웠던 점" in t
    assert "#성남분당카페" in t


def test_no_sponsor_no_note():
    v = {k: x for k, x in V.items() if k not in ("sponsored", "sponsor_provided")}; assert "제공받아" not in core.make(v, TODAY)


@pytest.mark.parametrize("patch,msg", [({"visited": "2026-12-01"}, "미래"), ({"visited": "10월 24일"}, "형식"), ({"menu": []}, "메뉴"), ({"menu": [{"name": "a"}]}, "느낀 점"), ({"sponsor_provided": ""}, "협찬"), ({"address": ""}, "빠진 항목")])
def test_refuses_without_real_visit(patch, msg):
    with pytest.raises(core.ReviewError, match=msg): core.make({**V, **patch}, TODAY)


def test_check():
    r = core.check("인생맛집 무조건 가세요", photos=2, sponsored=True); k = [x for x, _ in r]
    assert k.count("협찬") == 2 and k.count("과장") == 2 and "사진" in k and "날짜" in k
    assert core.check(core.make(V, TODAY), photos=5, sponsored=True) == []


def test_index_grouped_sorted():
    t = core.index(core.load(os.path.join(S, "visits_all.json")))
    assert t.index("## 서울 마포") < t.index("## 성남 분당") and t.index("국밥집") > t.index("카페 하루") and "· 협찬" in t


def test_load_error():
    with pytest.raises(core.ReviewError): core.load("/none.json")


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "r.md")
    assert main(["make", os.path.join(S, "visit.json"), "--out", out, "--today", "2026-10-27"]) == 0
    assert main(["check", out, "--photos", "5", "--sponsored"]) == 0 and main(["check", out, "--sponsored"]) == 1
    assert main(["index", os.path.join(S, "visits_all.json")]) == 0 and main(["make", str(tmp_path / "x.json")]) == 2
