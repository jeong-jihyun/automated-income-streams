import os
import numpy as np
import pytest
from PIL import Image
from profilephoto import bg, make
from profilephoto.bg import PhotoError
from profilephoto.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
SELFIE = Image.open(os.path.join(S, "selfie.jpg")); FACE = (300, 250, 300, 400)


def corner(im):
    return np.asarray(im)[2, 2]


def test_background_replaced_and_subject_kept():
    out, info = bg.replace(SELFIE, (255, 255, 255)); a = np.asarray(out).astype(int)
    assert info["ok"] and 0.2 < info["foreground"] < 0.8
    assert np.abs(a[5, 5] - 255).max() < 6 and np.abs(a[450, 450] - np.array([224, 172, 140])).max() < 20     # 가장자리=흰색, 얼굴 색 유지
    assert np.abs(a[1000, 450] - np.array([40, 60, 110])).max() < 20


def test_enclosed_hole_not_erased():
    im = Image.new("RGB", (300, 300), (200, 200, 200))
    from PIL import ImageDraw
    d = ImageDraw.Draw(im); d.rectangle((60, 60, 240, 240), fill=(10, 10, 10)); d.rectangle((120, 120, 180, 180), fill=(200, 200, 200))     # 안쪽 구멍은 배경색과 같다
    out, info = bg.replace(im, (255, 255, 255)); assert info["ok"] and np.abs(np.asarray(out)[150, 150].astype(int) - 200).max() < 6


def test_complex_background_refused():
    out, info = bg.replace(Image.open(os.path.join(S, "noisy_bg.jpg")), (255, 255, 255))
    assert not info["ok"] and "복잡" in info["reason"] and out.size == (900, 1200)


def test_crop_box_math():
    b = make.crop_box((900, 1200), (300, 250, 300, 400), 3 / 4, 0.5)
    assert b[3] - b[1] == 800 and b[2] - b[0] == 600 and abs((b[0] + b[2]) / 2 - 450) <= 1


def test_all_presets_exact_size():
    for k, (W, H, _, _) in make.PRESETS.items():
        out, notes = make.make(SELFIE, k, FACE); assert out.size == (W, H)


def test_pad_when_not_enough_margin_and_notes():
    out, notes = make.make(SELFIE, "id_35x45", (10, 10, 300, 300)); assert any("모자라" in n for n in notes)
    out, notes = make.make(SELFIE, "linkedin"); assert any("추정" in n for n in notes)


def test_face_box_validation_and_options():
    for bad in ((-5, 0, 100, 100), (0, 0, 0, 10), (800, 1100, 300, 300)):
        with pytest.raises(PhotoError, match="밖"): make.make(SELFIE, "linkedin", bad)
    with pytest.raises(PhotoError, match="규격"): make.make(SELFIE, "x", FACE)
    with pytest.raises(PhotoError, match="배경색"): make.make(SELFIE, "linkedin", FACE, "red")


def test_quality_checks(tmp_path):
    assert make.check(Image.new("RGB", (300, 300), (5, 5, 5)))[0].startswith("사진이 작아요")
    assert "너무 어두워요" in make.check(Image.new("RGB", (800, 800), (5, 5, 5))) and "너무 밝아요" in make.check(Image.new("RGB", (800, 800), (250, 250, 250)))


def test_colors_are_preserved_and_background_exact():
    out, _ = make.make(SELFIE, "resume_3x4", FACE, "blue"); a = np.asarray(out).astype(int)
    assert np.abs(a[5, 5] - np.array(make.COLORS["blue"])).max() <= 12                    # 배경이 고른 색에 가깝다
    skin = a[150, 177]; assert skin[0] > skin[1] > skin[2] and abs(skin[0] - 224) < 40 and abs(skin[2] - 140) < 40      # 피부색이 주황/하늘색으로 변하지 않는다
    shirt = a[440, 177]; assert shirt[2] > shirt[0] and shirt.max() > 40 and shirt.max() < 160                             # 옷이 검정으로 뭉개지지 않는다


def test_light_gain_limits():
    dark, g = make.normalize_light(Image.new("RGB", (50, 50), (20, 20, 20))); assert g == 1.2
    bright, g2 = make.normalize_light(Image.new("RGB", (50, 50), (250, 250, 250))); assert g2 == 0.85
    same, g3 = make.normalize_light(Image.new("RGB", (50, 50), (128, 128, 128))); assert abs(g3 - 1) < 0.01


def test_id_preset_warns_not_official():
    assert "제출용 아님" in make.PRESETS["id_35x45"][3]


def test_cli(tmp_path, capsys):
    out = str(tmp_path / "o.jpg")
    assert main([os.path.join(S, "selfie.jpg"), "--preset", "resume_3x4", "--face", "300,250,300,400", "--color", "blue", "--out", out]) == 0
    assert Image.open(out).size == (354, 472) and "이력서" in capsys.readouterr().out
    assert main([os.path.join(S, "selfie.jpg"), "--face", "1,2,3", "--out", out]) == 2 and main([str(tmp_path / "no.jpg"), "--out", out]) == 2
