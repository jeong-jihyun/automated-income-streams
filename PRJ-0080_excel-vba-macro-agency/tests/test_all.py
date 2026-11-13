import os
from vbacheck import core
from vbacheck.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample")
RISKY, CLEAN = os.path.join(D, "risky.bas"), os.path.join(D, "clean.bas")


def names(path):
    f, _ = core.scan(open(path, encoding="utf-8").read()); return {x["name"] for x in f}, f


def test_risky_finds_everything():
    n, _ = names(RISKY)
    assert {"외부 프로그램 실행", "파일 삭제", "외부 객체 생성", "자동 실행", "오류 무시", "고정 경로",
            "Select·Activate 사용", "화면 갱신 끄기", "Option Explicit 없음", "암호가 코드에 적힘"} <= n


def test_clean_has_nothing():
    f, n = core.scan(open(CLEAN, encoding="utf-8").read()); assert f == [] and n == 6


def test_comments_ignored_but_quote_in_string_kept():
    assert core.strip_line("x = 1 ' Kill a") == "x = 1 "
    assert core.strip_line('s = "a'"'"'b" : Kill f').count("Kill") == 1
    assert core.strip_line("Rem Kill f") == ""


def test_sorted_by_severity_then_line():
    _, f = names(RISKY); sev = [core.ORDER[x["sev"]] for x in f]; assert sev == sorted(sev)


def test_line_numbers():
    _, f = names(RISKY); d = {x["name"]: x["line"] for x in f}
    assert d["파일 삭제"] == 7 and d["외부 프로그램 실행"] == 8 and d["자동 실행"] == 2


def test_option_explicit_in_comment_does_not_count():
    f, _ = core.scan("' Option Explicit\nSub A()\nEnd Sub\n"); assert any(x["name"] == "Option Explicit 없음" for x in f)


def test_verdict():
    assert core.verdict([]) == "발견된 것 없음"
    assert core.verdict([{"sev": core.L}]) == "주의 사항 있음"
    assert core.verdict([{"sev": core.H}]) == "납품 전 확인 필요"


def test_report_has_limit_note():
    f, n = core.scan(open(RISKY, encoding="utf-8").read()); t = core.report("risky.bas", f, n)
    assert "실행해 보지 않았습니다" in t and "납품 전 확인 필요" in t


def test_cli_exit_codes(capsys):
    assert main([RISKY]) == 1 and main([CLEAN]) == 0 and main(["nope.bas"]) == 2
