import json
import os
from datetime import datetime
import pytest
from PIL import Image
from insta_tool import posts, replies
from insta_tool.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
CSV = os.path.join(S, "posts.csv")
RULES = replies.load_rules(os.path.join(S, "rules.json"))


def test_sample_clean():
    assert posts.check(posts.load(CSV), S) == []


def test_post_problems(tmp_path):
    Image.new("RGB", (3000, 500)).save(tmp_path / "wide.jpg"); Image.new("RGB", (200, 200)).save(tmp_path / "small.jpg")
    rows = [{"id": "1", "when": "2031-13-01 09:00", "image": "wide.jpg", "caption": "x" * 2201},
            {"id": "1", "when": "2031-03-01 09:00", "image": "small.jpg", "caption": " ".join(f"#t{i}" for i in range(31))},
            {"id": "3", "when": "2031-03-01 09:30", "image": "none.jpg", "caption": "#a #A"}]
    msgs = " | ".join(m for _, m in posts.check(rows, str(tmp_path)))
    for key in ("중복", "YYYY-MM-DD", "2200자", "비율", "30개", "너무 작", "열 수 없", "반복"):
        assert key in msgs, key
    assert posts.find_conflicts([{"id": "a", "when": "2031-03-01 09:00"}, {"id": "b", "when": "2031-03-01 09:30"}, {"id": "c", "when": "2031-03-01 12:00"}]) == [("a", "b")]


def test_due_and_missing_columns(tmp_path):
    rows = posts.load(CSV)
    assert [r["id"] for r in posts.due(rows, datetime(2031, 3, 1, 9, 0))] == ["1"]
    assert [r["id"] for r in posts.due(rows, datetime(2031, 3, 5), done_ids={"1"})] == ["2"]
    assert posts.due(rows, datetime(2031, 2, 1)) == []
    f = tmp_path / "b.csv"; f.write_text("id,when\n1,x\n")
    with pytest.raises(posts.PostError): posts.load(str(f))


def test_classify():
    c = lambda t: replies.classify(RULES, {"user": "가나", "text": t})
    assert c("가격이 얼마예요?")["reply"].startswith("가나님, 가격은")
    assert c("영업시간 알려주세요")["action"] == "reply"
    assert c("대출 상담 https://x.com")["action"] == "ignore"
    assert c("서비스 최악이네요 가격도 비싸고")["action"] == "human"     # 부정이 규칙보다 우선
    assert c("예뻐요")["action"] == "human"
    assert replies.classify(RULES, {"text": "가격?"})["reply"].startswith("고객님")


def test_plan_limits_and_dedupe():
    cfg = dict(RULES, max_replies_per_hour=2)
    cs = [{"id": str(i), "user": "u", "text": "가격?"} for i in range(4)]
    out = replies.plan(cfg, cs, replied_ids={"0"})
    assert [o["action"] for o in out] == ["reply", "reply", "human"] and out[-1]["reason"].startswith("시간당")
    assert [o["action"] for o in replies.plan(cfg, cs, replies_last_hour=2)] == ["human"] * 4


def test_rule_errors(tmp_path):
    f = tmp_path / "r.json"
    for txt in ("{", '{"rules": []}', '{"rules": [{"name": "a", "keywords": []}]}'):
        f.write_text(txt)
        with pytest.raises(replies.RuleError): replies.load_rules(str(f))


def test_cli(tmp_path, capsys):
    assert main(["check", "--csv", CSV]) == 0
    assert main(["due", "--csv", CSV, "--now", "2031-03-03 00:00", "--done", "1"]) == 0 and "#2" in capsys.readouterr().out
    cm = tmp_path / "c.json"; cm.write_text(json.dumps([{"id": "1", "user": "가", "text": "가격?"}]), encoding="utf-8")
    assert main(["replies", "--rules", os.path.join(S, "rules.json"), "--comments", str(cm)]) == 0 and "사람이 확인" in capsys.readouterr().out
    assert main(["check", "--csv", str(tmp_path / "x.csv")]) == 2
