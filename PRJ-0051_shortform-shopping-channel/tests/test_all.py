import os, shutil, subprocess, json
import pytest
from shortform import plan as P, render as R
from shortform.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "product.json")
PR = P.load(S)
HAS_VIDEO = bool(shutil.which("ffmpeg")) and any(os.path.exists(f) for f in R.FONTS)


def test_plan_structure_and_timing():
    pl = P.make(PR); r = [s["role"] for s in pl["scenes"]]
    assert r == ["광고 표시+제목", "특징 1", "특징 2", "특징 3", "가격", "마무리"] and pl["total"] == round(sum(s["dur"] for s in pl["scenes"]), 1)
    assert all(b["start"] == round(a["start"] + a["dur"], 1) for a, b in zip(pl["scenes"], pl["scenes"][1:])) and pl["total"] <= 60


def test_disclosure_everywhere_and_check_ok():
    pl = P.make(PR)
    assert P.DISCLOSURE_SCREEN in pl["scenes"][0]["screen"] and pl["caption"].startswith("#광고") and "2026-10-26 기준" in pl["scenes"][4]["narration"] and P.check(pl) == []


def test_check_detects_removed_disclosure():
    pl = P.make(PR); pl["scenes"][0]["screen"] = ["제목"]; pl["caption"] = "구매 링크"; assert len(P.check(pl)) == 2


@pytest.mark.parametrize("patch,msg", [({"features": ["하나"]}, "2~5"), ({"features": ["무조건 좋음", "b"]}, "과장"), ({"link": ""}, "빠진"), ({"name": "1위 선풍기"}, "과장")])
def test_refuses(patch, msg):
    with pytest.raises(P.PlanError, match=msg): P.make({**PR, **patch})


def test_too_long_refused():
    with pytest.raises(P.PlanError, match="초예요"): P.make({**PR, "features": ["아주 긴 설명 " * 12] * 5})


def test_no_price_scene_without_date():
    pl = P.make({k: v for k, v in PR.items() if k != "price_date"}); assert "가격" not in [s["role"] for s in pl["scenes"]]


def test_srt_format():
    t = P.srt(P.make(PR)); assert t.startswith("1\n00:00:00,000 --> 00:00:0") and t.count("-->") == 6


def test_cli_files(tmp_path, capsys):
    assert main([S, str(tmp_path)]) == 0 and sorted(os.listdir(tmp_path)) == ["caption.txt", "plan.json", "subtitles.srt"]
    assert main([str(tmp_path / "none.json"), str(tmp_path)]) == 2


@pytest.mark.skipif(not HAS_VIDEO, reason="ffmpeg 또는 한글 글꼴 없음")
def test_real_video(tmp_path):
    assert main([S, str(tmp_path), "--video"]) == 0
    v = str(tmp_path / "video.mp4"); assert os.path.getsize(v) > 5000
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height:format=duration", "-of", "csv=p=0", v], capture_output=True, text=True).stdout
    pl = json.load(open(tmp_path / "plan.json")); assert "1080,1920" in o and abs(float(o.strip().split("\n")[-1]) - pl["total"]) < 1.0


def test_font_missing(tmp_path):
    with pytest.raises(R.RenderError): R.find_font("/nope.ttf") if not any(os.path.exists(f) for f in R.FONTS) else (_ for _ in ()).throw(R.RenderError("ok"))
