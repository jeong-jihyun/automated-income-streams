import csv, math, os, struct, wave
import pytest
from bgm_catalog import core
from bgm_catalog.cli import main

HEAD = core.REQUIRED


def sine(path, sec, freq=440, rate=22050):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
        w.writeframes(b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / rate)))
            for i in range(int(sec * rate))))


def write_csv(path, rows, head=HEAD):
    with open(path, "w", encoding="utf-8", newline="") as f:
        wr = csv.writer(f); wr.writerow(head)
        for r in rows: wr.writerow(r)


def good(i, file):
    return [f"T{i}", f"곡 {i}", file, "밝음", "팝", "120", "self", "", "직접 작곡", ""]


@pytest.fixture
def env(tmp_path):
    m = tmp_path / "music"; m.mkdir()
    sine(str(m / "a.wav"), 40); sine(str(m / "b.wav"), 5, 330)
    return tmp_path, m


def test_validate_ok(env):
    t, m = env
    write_csv(t / "t.csv", [good(1, "a.wav"), good(2, "b.wav")])
    cols, rows = core.read_rows(str(t / "t.csv"))
    assert core.validate(cols, rows, str(m)) == []


def test_missing_rights_basis_detected(env):
    t, m = env
    r = good(1, "a.wav"); r[8] = ""
    write_csv(t / "t.csv", [r])
    cols, rows = core.read_rows(str(t / "t.csv"))
    assert any("권리 근거" in p[2] for p in core.validate(cols, rows, str(m)))


def test_ai_track_needs_tool_and_date(env):
    t, m = env
    r = good(1, "a.wav"); r[6] = "ai"
    write_csv(t / "t.csv", [r])
    cols, rows = core.read_rows(str(t / "t.csv"))
    msgs = " ".join(p[2] for p in core.validate(cols, rows, str(m)))
    assert "도구" in msgs and "약관 확인일" in msgs


def test_duplicate_id_missing_file_bad_bpm_bad_date(env):
    t, m = env
    a = good(1, "a.wav"); b = good(1, "nofile.wav"); b[5] = "abc"; b[9] = "2026/1/1"
    write_csv(t / "t.csv", [a, b])
    cols, rows = core.read_rows(str(t / "t.csv"))
    msgs = " ".join(p[2] for p in core.validate(cols, rows, str(m)))
    for key in ("겹칩니다", "음악 파일이 없습니다", "BPM", "YYYY-MM-DD"):
        assert key in msgs


def test_missing_columns(env):
    t, m = env
    write_csv(t / "t.csv", [["T1", "x"]], head=["id", "title"])
    cols, rows = core.read_rows(str(t / "t.csv"))
    assert "필수 열" in core.validate(cols, rows, str(m))[0][2]


def test_empty_csv_and_missing_csv(env):
    t, m = env
    write_csv(t / "e.csv", [])
    with pytest.raises(ValueError): core.read_rows(str(t / "e.csv"))
    with pytest.raises(FileNotFoundError): core.read_rows(str(t / "none.csv"))


def test_preview_length_and_short_track(env):
    t, m = env
    core.make_preview(str(m / "a.wav"), str(t / "p1.mp3"))
    core.make_preview(str(m / "b.wav"), str(t / "p2.mp3"))
    assert 29 <= core.probe_duration(str(t / "p1.mp3")) <= 31.5
    assert 4 <= core.probe_duration(str(t / "p2.mp3")) <= 6


def test_full_run_builds_site_with_right_count(env):
    t, m = env
    write_csv(t / "t.csv", [good(1, "a.wav"), good(2, "b.wav")])
    out = t / "out"
    res = core.run(str(t / "t.csv"), str(m), str(out))
    assert res["ok"] and res["tracks"] == 2
    page = (out / "index.html").read_text(encoding="utf-8")
    assert page.count("class='track'") == 2 and "총 2곡" in page
    assert (out / "previews" / "T1.mp3").exists()
    assert "초안" in (out / "LICENSE_GUIDE.md").read_text(encoding="utf-8")


def test_html_is_escaped(env):
    t, m = env
    r = good(1, "a.wav"); r[1] = "<script>alert(1)</script>"
    write_csv(t / "t.csv", [r])
    out = t / "out"
    core.run(str(t / "t.csv"), str(m), str(out))
    page = (out / "index.html").read_text(encoding="utf-8")
    assert "<script>alert" not in page and "&lt;script&gt;" in page


def test_validation_failure_creates_no_files(env):
    t, m = env
    r = good(1, "a.wav"); r[8] = ""
    write_csv(t / "t.csv", [r])
    out = t / "out"
    res = core.run(str(t / "t.csv"), str(m), str(out))
    assert not res["ok"] and not out.exists()


def test_cli_exit_codes(env, capsys):
    t, m = env
    write_csv(t / "t.csv", [good(1, "a.wav")])
    assert main([str(t / "t.csv"), str(m), str(t / "o")]) == 0
    assert main([str(t / "nofile.csv"), str(m), str(t / "o2")]) == 2
