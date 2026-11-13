import json, os
import pytest
from dispatchq import core
from dispatchq.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample"); T, R = os.path.join(D, "templates.json"), os.path.join(D, "recipients.csv")


def run(name, at="10:00"):
    return core.build(core.load_templates(T)[name], core.read_recipients(R), at)


def test_phone_normalize():
    assert core.norm_phone("010-1234-5678") == "01012345678" and core.norm_phone("+82 10-5555-6666") == "01055556666"
    assert core.norm_phone("02-123-4567") is None and core.norm_phone("") is None


def test_info_template_skips_and_dedupes():
    out, sk = run("reminder"); reasons = dict(sk)
    assert [m["to"] for m in out] == ["01012345678", "01099998888", "01077778888"]
    assert reasons[4] == "휴대폰 번호 형식 오류" and reasons[5].startswith("채울 값 없음") and reasons[6].startswith("같은 번호")


def test_ad_requires_consent_and_marking():
    out, sk = run("event"); assert "광고 수신 동의 없음" in dict(sk).values()
    assert all(m["text"].startswith("(광고) ") and "무료수신거부" in m["text"] for m in out) and len(out) == 3


def test_ad_blocked_in_quiet_hours():
    out, sk = run("event", "21:30"); assert out == [] and any("광고 금지 시간대" in w for _, w in sk)
    out, _ = run("reminder", "23:00"); assert len(out) == 3      # 정보성은 시간 제한 없음(이 도구 기준)


def test_quiet_boundaries():
    assert core.is_quiet("21:00") and core.is_quiet("07:59") and not core.is_quiet("08:00") and not core.is_quiet("20:59")
    with pytest.raises(ValueError):
        core.is_quiet("25:00")


def test_sms_lms_by_bytes():
    assert core.size_kind("가" * 45) == ("SMS", None) and core.size_kind("가" * 46) == ("LMS", None)
    assert core.size_kind("가" * 1001)[1] == "2000바이트 초과" and core.size_kind("😀")[1].startswith("표현할 수 없는")


def test_bad_template(tmp_path):
    p = tmp_path / "t.json"; p.write_text('{"a": {"text": "x", "kind": "spam"}}', encoding="utf-8")
    with pytest.raises(ValueError):
        core.load_templates(str(p))


def test_cli_writes_outbox_only(tmp_path, capsys):
    o = tmp_path / "o.jsonl"; assert main([T, "reminder", R, "--out", str(o)]) == 0
    lines = [json.loads(l) for l in o.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 3 and all(l["status"] == "READY" for l in lines) and "발송은 하지 않았습니다" in capsys.readouterr().out
    assert main([T, "nope", R]) == 2 and main([T, "reminder", "x.csv"]) == 2
