import copy, json, os, re, zipfile
import pytest
from pypdf import PdfReader
from video_preset import config, subs, preview, package
from video_preset.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "sample", "styles.json")
FONTS = {"noto sans cjk kr"}
needs_ffmpeg = pytest.mark.skipif(not preview.have_ass_filter(), reason="ffmpeg ass 필터 없음")


def cfg():
    return config.load(SAMPLE)


def test_sample_is_valid():
    p, w = config.validate(cfg(), fonts=FONTS)
    assert p == [] and w == []  # 글꼴 라이선스가 적혀 있으면 경고 없음 (글꼴 파일 포함 가능 여부는 체크리스트에서)


def test_bad_values_detected():
    c = cfg()
    c["styles"][0].update(color="red", size=999, alignment=0, font="없는글꼴")
    c["styles"][1]["id"] = c["styles"][0]["id"]
    c["styles"][1]["outline_color"] = "#12345"
    p, _ = config.validate(c, fonts=FONTS)
    msg = " ".join(p)
    for key in ("color 색 값 오류", "size 은 10~200", "alignment 은 1~9", "설치되어 있지 않음", "id 가 겹침", "outline_color 색 값 오류"):
        assert key in msg, key


def test_bool_and_missing_number_rejected():
    c = cfg(); c["styles"][0]["size"] = True; c["styles"][0]["outline"] = "3"
    p, _ = config.validate(c, fonts=FONTS)
    assert sum("숫자" in m for m in p) == 2


def test_unlisted_font_warns():
    c = cfg(); c["fonts"] = []
    _, w = config.validate(c, fonts=FONTS)
    assert any("라이선스 정보가 fonts 목록에 없음" in x for x in w)


def test_load_errors(tmp_path):
    with pytest.raises(FileNotFoundError): config.load(str(tmp_path / "x.json"))
    (tmp_path / "bad.json").write_text("{not json")
    with pytest.raises(ValueError): config.load(str(tmp_path / "bad.json"))
    (tmp_path / "e.json").write_text(json.dumps({"pack_name": "a", "styles": []}))
    with pytest.raises(ValueError): config.load(str(tmp_path / "e.json"))


def test_color_and_time_conversion():
    assert subs.ass_color("#FF8800") == "&H000088FF"
    assert subs.ass_time(3661.5) == "1:01:01.50"
    assert subs.srt_time(3661.5) == "01:01:01,500"


def test_ass_structure_and_times():
    c = cfg()
    ass = subs.build_ass(c["styles"], c["resolution"])
    assert "PlayResX: 1280" in ass and ass.count("\nStyle: ") == 2 and ass.count("Dialogue: ") == 2
    assert "{\\fad(150,150)}" in ass and "{\\fad(0,300)}" in ass
    for m in re.finditer(r"Dialogue: 0,(\S+?),(\S+?),", ass):
        assert subs.ASS_TIME.match(m.group(1)) and subs.ASS_TIME.match(m.group(2))
    assert "0:00:03.00,0:00:06.00,fun-02" in ass  # 두 번째 스타일은 3초 뒤


def test_srt_structure():
    c = cfg()
    srt = subs.build_srt(c["styles"])
    blocks = srt.strip().split("\n\n")
    assert len(blocks) == 2
    for i, b in enumerate(blocks, 1):
        lines = b.split("\n")
        assert lines[0] == str(i)
        a, _, z = lines[1].partition(" --> ")
        assert subs.SRT_TIME.match(a) and subs.SRT_TIME.match(z)


def test_multiline_text_uses_ass_break():
    c = cfg(); c["styles"][0]["sample_text"] = "첫 줄\n둘째 줄"
    assert "첫 줄\\N둘째 줄" in subs.build_ass(c["styles"], c["resolution"])


@needs_ffmpeg
def test_preview_size_and_length(tmp_path):
    c = cfg()
    ap = tmp_path / "a.ass"
    ap.write_text(subs.build_ass(c["styles"], c["resolution"], one_style_only="fun-01"), encoding="utf-8")
    mp4, gif = preview.make_preview(str(ap), str(tmp_path / "p"), "fun-01", c["resolution"], c["background"])
    info = preview.probe(mp4)
    assert (info["width"], info["height"]) == (1280, 720) and abs(info["duration"] - 3.0) < 0.2
    assert os.path.getsize(gif) > 1000


def test_checklist_marks_unknown():
    c = cfg()
    text = package.font_checklist(c)
    assert "확인 필요" in text and "Noto Sans CJK KR" in text
    c["fonts"][0]["redistribute"] = True
    assert "| 가능 |" in package.font_checklist(c)
    c["fonts"] = []
    assert "정보 없음" in package.font_checklist(c)


def test_guide_pdf_pages(tmp_path):
    out = str(tmp_path / "g.pdf")
    n = package.guide_pdf(out, cfg())
    assert n == len(PdfReader(out).pages) == 4


def test_cli_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "installed_fonts", lambda: FONTS)
    out = tmp_path / "out"
    assert main(["build", "--config", SAMPLE, "--out", str(out)]) == 0
    z = zipfile.ZipFile(out / "preset_pack.zip").namelist()
    assert "guide.pdf" in z and "ass/fun-01.ass" in z and "srt/fun-02.srt" in z
    if preview.have_ass_filter():
        assert "previews/fun-01.mp4" in z and "previews/fun-02.gif" in z
    assert (out / "listing_draft.txt").exists()


def test_cli_blocks_bad_config(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "installed_fonts", lambda: FONTS)
    c = cfg(); c["styles"][0]["color"] = "nope"
    bad = tmp_path / "b.json"; bad.write_text(json.dumps(c))
    out = tmp_path / "o"
    assert main(["build", "--config", str(bad), "--out", str(out)]) == 1 and not out.exists()
    assert main(["check", "--config", str(tmp_path / "none.json")]) == 2
