import json, os, shutil, subprocess
import pytest
from clipcut import core
from clipcut.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "live.srt")
CUES = core.parse_srt(open(S, encoding="utf-8").read()); KW = ["접이식 선풍기", "선풍기"]


def test_parse_srt():
    assert len(CUES) == 6 and CUES[2]["start"] == 20.0 and CUES[2]["end"] == 34.0 and "29,900원" in CUES[2]["text"]
    assert core.parse_srt("1\n00:00:01.5 --> 00:00:03.25\n안녕")[0]["end"] == 3.25                      # 점 구분·소수 자리


def test_parse_errors():
    with pytest.raises(core.ClipError, match="시간 구간"): core.parse_srt("그냥 글")
    with pytest.raises(core.ClipError, match="거꾸로"): core.parse_srt("1\n00:00:05,000 --> 00:00:01,000\nx")


def test_score_components():
    assert core.score("접이식 선풍기", KW) == 6 and core.score("29,900원 쿠폰", []) == 4 and core.score("지금 링크", []) == 3 and core.score("날씨 이야기", KW) == 0


def test_candidates_length_limits():
    for c in core.candidates(CUES, KW): assert 15 <= c["len"] <= 45


def test_pick_no_overlap_and_best_selling_part():
    ps = core.pick(CUES, KW, top=3)
    assert all(a["end"] <= b["start"] for a, b in zip(ps, ps[1:])) and any("29,900원" in p["text"] for p in ps)
    assert all(15 <= p["len"] <= 45 for p in ps) and len(ps) <= 3


def test_weather_only_section_not_chosen():
    ps = core.pick(core.parse_srt(open(S, encoding="utf-8").read()), KW, top=5)
    assert not any(p["start"] >= 50 and p["end"] <= 70 for p in ps)                                   # 날씨 구간 단독 선택 없음


def test_flags_exaggeration():
    ps = core.pick(CUES, KW, top=5); assert any(any("무조건" in f for f in p["flags"]) for p in ps)


def test_no_keywords_no_signals_gives_nothing():
    assert core.pick(core.parse_srt("1\n00:00:00,000 --> 00:00:30,000\n그냥 잡담이에요"), []) == []


def test_srt_for_rebased():
    c = {"start": 20.0, "end": 34.0}; t = core.srt_for(c, CUES); assert t.startswith("1\n00:00:00,000 --> 00:00:14,000") and t.count("-->") == 1


HAS_FF = bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe"))


@pytest.fixture(scope="module")
def video(tmp_path_factory):
    v = str(tmp_path_factory.mktemp("v") / "live.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=s=1280x720:r=15:d=95", "-f", "lavfi", "-i", "sine=f=440:d=95", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", v], check=True)
    return v


@pytest.mark.skipif(not HAS_FF, reason="ffmpeg 없음")
def test_real_cut_duration_and_vertical(video, tmp_path):
    c = {"start": 20.0, "end": 34.0}; out = core.cut(video, c, str(tmp_path / "c.mp4"))
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    assert abs(d - 14.0) < 1.0
    v = core.cut(video, c, str(tmp_path / "v.mp4"), vertical=True)
    wh = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", v], capture_output=True, text=True).stdout.strip(); assert wh == "1080,1920"


@pytest.mark.skipif(not HAS_FF, reason="ffmpeg 없음")
def test_cli_with_video(video, tmp_path, capsys):
    out = str(tmp_path / "o"); assert main([S, "--video", video, "--out", out, "--keywords", "선풍기", "--top", "2"]) == 0
    assert os.path.exists(os.path.join(out, "clip1.mp4")) and os.path.exists(os.path.join(out, "clip1.srt")) and json.load(open(os.path.join(out, "clips.json")))


def test_cli_errors(tmp_path):
    assert main([str(tmp_path / "none.srt")]) == 2
    e = tmp_path / "e.srt"; e.write_text("1\n00:00:00,000 --> 00:00:30,000\n잡담"); assert main([str(e), "--out", str(tmp_path / "o")]) == 1
