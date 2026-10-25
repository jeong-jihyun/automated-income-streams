import json
import os
import pytest
from PIL import Image
from foodcal import estimate as E, log, nutrition as N, photo
from foodcal.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample", "meal_sharp.jpg")


def test_estimate_math_and_range():
    r = E.one("쌀밥", "M"); assert r["grams"] == 210 and r["kcal"] == 315 and r["low"] == 236 and r["high"] == 394
    assert E.one("쌀밥", "100g")["kcal"] == 150 and E.one("쌀밥", "L")["grams"] == 294
    assert E.one("쌀밥", "M", 0.4)["high"] > r["high"] and E.one("쌀밥", "M", 0.4)["confirm"] and not r["confirm"]


def test_every_food_is_sane():
    for name, (k, c, p, f, srv) in N.FOODS.items():
        assert 5 <= k <= 600 and 10 <= srv <= 800
        assert 4 * c + 4 * p + 9 * f <= k * 1.5 + 30 and 4 * c + 4 * p + 9 * f >= k * 0.4, name        # 영양소 합과 칼로리가 크게 어긋나지 않음


def test_unknown_food_not_invented():
    res = E.estimate([("쌀밥", "M", 1.0), ("외계음식", "M", 0.9)])
    assert res["unknown"] == ["외계음식"] and len(res["rows"]) == 1 and res["kcal"] == 315 and "목록에 없어" in E.text(res)


def test_portion_validation():
    for bad in ("XL", "abcg", "1g", "9999g"):
        with pytest.raises(N.FoodError): E.one("쌀밥", bad)


def test_text_has_disclaimer_no_diet_advice():
    t = E.text(E.estimate([("김치", "S", 1.0), ("쌀밥", "M", 0.5)]))
    assert "대략" in t and "식단 지시가 아닙니다" in t and "확인해 주세요" in t
    for w in ("줄이세요", "감량", "목표 칼로리", "다이어트"): assert w not in t
    assert "직접 입력" in E.text(E.estimate([]))


def test_photo_checks(tmp_path):
    assert photo.check_photo(S)["ok"]
    Image.new("RGB", (400, 400), (5, 5, 5)).save(tmp_path / "dark.jpg")
    assert "너무 어두워요" in photo.check_photo(str(tmp_path / "dark.jpg"))["problems"]
    Image.new("RGB", (100, 100), (200, 100, 50)).save(tmp_path / "small.jpg")
    assert any("작아요" in x for x in photo.check_photo(str(tmp_path / "small.jpg"))["problems"])
    (tmp_path / "x.jpg").write_text("no"); assert not photo.check_photo(str(tmp_path / "x.jpg"))["ok"]
    with pytest.raises(FileNotFoundError): photo.check_photo(str(tmp_path / "none.jpg"))


def test_recognize_hook():
    r = photo.recognize(S, lambda p: [("쌀밥", 0.9), ("김치", 0.2), ("된장찌개", 0.5)])
    assert [i[0] for i in r["items"]] == ["쌀밥", "된장찌개"]
    def boom(p): raise RuntimeError("x")
    assert photo.recognize(S, boom)["items"] == [] and "직접 입력" in photo.recognize(S, boom)["problems"][0]
    assert photo.recognize(S, lambda p: None)["items"] == []


def test_day_log(tmp_path):
    f = str(tmp_path / "l.json")
    log.add(f, "2026-10-25", "점심", E.estimate([("쌀밥", "M", 1)])); log.add(f, "2026-10-25", "저녁", E.estimate([("김밥", "M", 1)]))
    d = log.day(f, "2026-10-25"); assert len(d["meals"]) == 2 and d["kcal"] == 315 + 391 and log.day(f, "2026-01-01")["kcal"] == 0


def test_cli(tmp_path, capsys):
    f = str(tmp_path / "l.json")
    assert main(["check-photo", S]) == 0 and "좋아요" in capsys.readouterr().out
    assert main(["estimate", "--item", "쌀밥=M", "--item", "김치=30g", "--log", f, "--date", "2026-10-25"]) == 0 and "합계 대략" in capsys.readouterr().out
    assert main(["day", f, "--date", "2026-10-25"]) == 0 and "끼니 1개" in capsys.readouterr().out
    assert main(["estimate", "--item", "쌀밥"]) == 2 and main(["check-photo", str(tmp_path / "no.jpg")]) == 2
