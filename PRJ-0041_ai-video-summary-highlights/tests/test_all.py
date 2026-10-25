import os
import shutil
import subprocess
import pytest
from vidsum import analyze, cut, parse, report
from vidsum.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "lecture.srt")
CUES = parse.parse(open(S, encoding="utf-8").read())
SEGS = analyze.score(analyze.segments(CUES, 100))


def test_parse_srt_vtt_and_noise():
    srt = "1\n00:00:01,500 --> 00:00:03,000\n<i>안녕하세요</i> 여러분\n\n2\n00:01:00,000 --> 00:01:02,250\n둘째 줄\n"
    c = parse.parse(srt); assert c == [(1.5, 3.0, "안녕하세요 여러분"), (60.0, 62.25, "둘째 줄")]
    vtt = "WEBVTT\n\n00:05.000 --> 00:07.500\n짧은 시간 형식\n\n01:00:00.000 --> 01:00:01.000\n한 시간 뒤\n"
    v = parse.parse(vtt); assert v[0] == (5.0, 7.5, "짧은 시간 형식") and v[1][0] == 3600.0
    assert parse.parse("2\n00:00:09,000 --> 00:00:10,000\n나중\n\n1\n00:00:01,000 --> 00:00:02,000\n먼저\n")[0][2] == "먼저"
    for bad in ("", "그냥 글", "1\n00:00:05,000 --> 00:00:01,000\n거꾸로\n"):
        with pytest.raises(parse.VideoError): parse.parse(bad)


def test_sample_parses():
    assert len(CUES) == 60 and CUES[-1][1] == 299.0


def test_segments_cover_everything_in_order():
    segs = analyze.segments(CUES, 100)
    assert len(segs) == 3 and segs[0]["start"] == 0 and segs[-1]["end"] == 299.0 and sum(len(s["cues"]) for s in segs) == 60
    assert all(segs[i]["end"] <= segs[i + 1]["start"] + 1 for i in range(2))


def test_titles_follow_topics():
    assert "변수" in SEGS[0]["title"] and "반복문" in SEGS[1]["title"] and "함수" in SEGS[2]["title"]


def test_summary_and_highlights():
    s = analyze.summary(SEGS, 3); assert len(s) == 3 and all(isinstance(x, str) and x for x in s)
    h = analyze.highlights(SEGS, 2); assert len(h) == 2 and h[0]["start"] < h[1]["start"] and all(0 <= x["start"] < x["end"] <= 299 for x in h)
    long_h = analyze.highlights(SEGS, 3, max_len=30); assert all(x["end"] - x["start"] <= 30 for x in long_h)
    assert analyze.highlights(SEGS, 3, min_len=500) == []


def test_report_text():
    md = report.markdown("강의", SEGS, analyze.highlights(SEGS, 2), analyze.summary(SEGS))
    assert "한눈에 보기" in md and "00:01:40" in md and "영상 화면·소리는 분석하지 않았고" in md and "저작권" in md


def test_cut_command_and_errors(tmp_path):
    cmd = cut.command("in.mp4", {"start": 1.5, "end": 4.0}, "out.mp4"); assert cmd[cmd.index("-ss") + 1] == "1.500" and cmd[cmd.index("-to") + 1] == "4.000" and cmd[-1] == "out.mp4"
    with pytest.raises(parse.VideoError, match="없습니다"): cut.cut_all(str(tmp_path / "no.mp4"), [], str(tmp_path))
    (tmp_path / "v.mp4").write_bytes(b"x")
    class R: returncode, stderr = 1, "boom"
    with pytest.raises(parse.VideoError, match="자르기 실패"): cut.cut_all(str(tmp_path / "v.mp4"), [{"start": 0, "end": 1, "title": ""}], str(tmp_path / "o"), runner=lambda *a, **k: R())
    assert cut.ts(3725.5) == "01:02:05.500"


@pytest.mark.skipif(shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None, reason="ffmpeg 없음")
def test_real_cut_with_ffmpeg(tmp_path):
    v = str(tmp_path / "t.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc=size=160x120:rate=10", "-f", "lavfi", "-i", "sine=frequency=440", "-t", "6", "-c:v", "libx264", "-c:a", "aac", v], check=True)
    outs = cut.cut_all(v, [{"start": 1, "end": 3, "title": "a"}, {"start": 4, "end": 5.5, "title": "b"}], str(tmp_path / "o"))
    durs = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", o], capture_output=True, text=True).stdout) for o in outs]
    assert abs(durs[0] - 2.0) < 0.3 and abs(durs[1] - 1.5) < 0.3 and os.path.getsize(v) > 0


def test_cli_without_video(tmp_path, capsys):
    out = str(tmp_path / "o")
    assert main([S, "--out", out, "--window", "100", "--highlights", "2"]) == 0 and os.path.exists(os.path.join(out, "summary.md"))
    assert main([str(tmp_path / "none.srt"), "--out", out]) == 2
    (tmp_path / "b.srt").write_text("아무 내용"); assert main([str(tmp_path / "b.srt"), "--out", out]) == 2
    assert main([S, "--out", out, "--video", str(tmp_path / "no.mp4")]) == 2
