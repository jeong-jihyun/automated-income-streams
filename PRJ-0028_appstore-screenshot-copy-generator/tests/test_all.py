import json
import os
import pytest
from PIL import Image
from store_kit import copy, shots, spec
from store_kit.cli import main

APP = os.path.join(os.path.dirname(__file__), "..", "sample", "app.json")
A = json.load(open(APP, encoding="utf-8"))
FONT = shots.find_font()


def test_sample_clean():
    d = copy.draft(A)
    assert copy.validate(d, 3) == [] and d["app_store"]["keywords"] == "가계부,지출,예산,영수증,절약"
    assert d["play"]["short"].startswith("쉽고 빠른 지출 기록 — 사진 한 장으로")


def test_keywords_dedupe_and_trim():
    s, used = copy.keyword_string(["a", "A", " b ", "", "b"], 100); assert s == "a,b"
    s, used = copy.keyword_string(["가" * 40, "나" * 40, "다" * 40], 100)
    assert len(s) <= 100 and used == ["가" * 40, "나" * 40]


def test_validate_limits_claims_and_counts():
    d = copy.draft(A); d["app_store"]["title"] = "가" * 31; d["play"]["short"] = "최고의 앱 " + "x" * 80
    msgs = " | ".join(copy.validate(d, 1))
    assert "app_store.title: 31자" in msgs and "play.short" in msgs and "최고의" in msgs and "play: 스크린샷은 2~8장" in msgs
    assert copy.validate(copy.draft(A), 11)                                      # 11장은 둘 다 초과


def test_check_app_missing():
    assert any("screens" in e for e in copy.check_app({k: v for k, v in A.items() if k != "screens"}))


def test_make_shot_size_and_layout():
    base = os.path.dirname(APP)
    im = shots.make_shot(os.path.join(base, "shot1.png"), "영수증을 찍으면 끝", "#2E5BFF", spec.SIZES["ios_6.7"], FONT)
    assert im.size == (1290, 2796)
    assert im.getpixel((5, 5)) == (46, 91, 255)                                   # 배경색
    px = im.getpixel((1290 // 2, 2796 // 2)); assert px != (46, 91, 255)           # 가운데에 앱 화면
    band = im.crop((0, 100, 1290, 500)).convert("RGB")                          # 머리글 영역: 흰 글자 픽셀이 충분히 있어야 함
    white = sum(1 for p in band.getdata() if p == (255, 255, 255)); assert white > 5000
    bottom = im.crop((0, 2796 - 60, 1290, 2796)).convert("RGB")                   # 맨 아래 여백은 배경색뿐
    assert set(bottom.getdata()) == {(46, 91, 255)}


def test_text_fit_and_too_long():
    from PIL import ImageDraw
    d = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    f, lines, size = shots.fit_text(d, "짧은 문구", FONT, 1000, 400); assert size == 120 and len(lines) == 1
    f, lines, size = shots.fit_text(d, "긴 문구 " * 8, FONT, 1000, 400); assert size < 120 and len(lines) >= 2
    with pytest.raises(shots.ShotError, match="너무 길어"): shots.fit_text(d, "가" * 400, FONT, 300, 100)


def test_color_and_missing_image(tmp_path):
    for bad in ("#12", "zzzzzz"):
        with pytest.raises(shots.ShotError): shots.hex_rgb(bad)
    with pytest.raises(shots.ShotError, match="열 수 없습니다"): shots.make_shot(str(tmp_path / "x.png"), "a", "#000000", (500, 900), FONT)


def test_cli_build(tmp_path, capsys):
    out = tmp_path / "o"
    assert main(["build", "--app", APP, "--out", str(out), "--sizes", "play_phone"]) == 0
    assert sorted(os.listdir(out)) == ["play_phone_01.png", "play_phone_02.png", "play_phone_03.png", "store_copy.json"]
    assert Image.open(out / "play_phone_01.png").size == (1080, 1920) and "공식 안내" in capsys.readouterr().out
    assert main(["build", "--app", APP, "--out", str(out), "--sizes", "ipad"]) == 2
    assert main(["check", "--app", APP]) == 0 and main(["check", "--app", str(tmp_path / "no.json")]) == 2
