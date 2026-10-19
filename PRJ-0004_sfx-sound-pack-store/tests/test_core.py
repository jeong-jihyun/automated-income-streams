import math, struct, wave
import pytest
from sfx_builder import core, cli


def tone(path, secs=0.5, lead=0.3, tail=0.3, rate=44100, amp=0.3):
    n = lambda s: int(rate * s)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        fr = [0]*n(lead) + [int(amp*32767*math.sin(2*math.pi*440*i/rate)) for i in range(n(secs))] + [0]*n(tail)
        w.writeframes(struct.pack("<" + "h"*len(fr), *fr))


def test_safe_name():
    assert core.safe_name("문 소리 Door-Open!", "sfx", 3) == "sfx_03_door_open.wav"
    assert core.safe_name("한글", "sfx", 1) == "sfx_01_sound.wav"


def test_tags_and_warn():
    assert "door" in core.tag_candidates("door_open_01")
    assert core.warn_text("Best Ever Disney sound")


def test_quality():
    st = core.load_settings()
    assert core.quality_issues({"seconds": 0.01, "peak_db": -60, "rate": 44100}, st)
    assert core.quality_issues({"seconds": 1, "peak_db": 0.0, "rate": 44100}, st) == ["클리핑 위험"]
    assert core.quality_issues({"seconds": 1, "peak_db": -3, "rate": 44100}, st) == []


def test_bad_folder():
    with pytest.raises(NotADirectoryError):
        core.list_audio("/no/dir")


def test_build_pack_trims_and_normalizes(tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    tone(src / "Door Open.wav")
    tone(src / "click.wav", secs=0.2, amp=0.05)
    (src / "bad.wav").write_text("not audio")
    res = core.build_pack(src, tmp_path / "o", "sfx")
    assert len(res["rows"]) == 2 and len(res["skipped"]) == 1
    for r in res["rows"]:
        assert r["seconds"] < 0.5 + 0.3 + 0.3 - 0.2  # 앞뒤 무음이 잘림
        assert r["rate"] == 44100 and r["bits"] == 16
    assert (tmp_path / "o" / "list.csv").exists()


def test_empty_folder_cli(tmp_path, capsys):
    (tmp_path / "e").mkdir()
    assert cli.main([str(tmp_path / "e"), str(tmp_path / "o")]) == 1


def test_cli_full(tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    tone(src / "a.wav")
    tone(src / "b.wav")
    assert cli.main([str(src), str(tmp_path / "o"), "--theme", "Doors"]) == 0
    assert (tmp_path / "o" / "demo.mp3").exists() and (tmp_path / "o" / "description.txt").exists()
