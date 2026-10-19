import json
from PIL import Image
import pytest
from kakao_checker import core, cli

RULE = {"count": 3, "width": 360, "height": 360, "formats": ["PNG"], "max_kb": 150, "need_transparent": True}


def mk(p, size=(360, 360), mode="RGBA", fmt="PNG"):
    c = (255, 0, 0, 0) if mode == "RGBA" else (255, 0, 0)
    im = Image.new(mode, size, c)
    if mode == "RGBA":
        im.putpixel((0, 0), (0, 0, 0, 0))
        im.putpixel((5, 5), (255, 0, 0, 255))
    im.save(p, fmt)


def test_pass(tmp_path):
    for i in range(3):
        mk(tmp_path / f"a{i}.png")
    assert core.check_folder(tmp_path, RULE)["ok"]


def test_wrong_size_and_count(tmp_path):
    mk(tmp_path / "a.png", (100, 100))
    mk(tmp_path / "b.png")
    r = core.check_folder(tmp_path, RULE)
    assert not r["ok"] and r["count_problem"] and "크기" in r["files"]["a.png"][0]


def test_no_transparency(tmp_path):
    mk(tmp_path / "a.png", mode="RGB")
    assert any("투명" in x for x in core.check_file(tmp_path / "a.png", RULE))


def test_not_image(tmp_path):
    (tmp_path / "a.png").write_text("hi")
    assert core.check_file(tmp_path / "a.png", RULE) == ["이미지로 열 수 없는 파일"]


def test_empty_folder(tmp_path):
    r = core.check_folder(tmp_path, RULE)
    assert r["count"] == 0 and not r["ok"]


def test_bad_folder():
    with pytest.raises(NotADirectoryError):
        core.list_images("/no/such/dir")


def test_resize(tmp_path):
    src = tmp_path / "s"
    src.mkdir()
    mk(src / "a.png", (1000, 500))
    mk(src / "b.png", (50, 50))
    core.resize_all(src, tmp_path / "o", RULE)
    for f in (tmp_path / "o").iterdir():
        assert Image.open(f).size == (360, 360)
    assert Image.open(src / "a.png").size == (1000, 500)  # 원본 유지


def test_rename(tmp_path):
    mk(tmp_path / "x.png")
    mk(tmp_path / "y.png")
    plan = core.rename_files(tmp_path, "emo", dry_run=True)
    assert plan == [("x.png", "emo_01.png"), ("y.png", "emo_02.png")] and (tmp_path / "x.png").exists()
    core.rename_files(tmp_path, "emo")
    assert (tmp_path / "emo_01.png").exists() and not (tmp_path / "x.png").exists()


def test_preset_and_cli(tmp_path, capsys):
    assert core.load_preset("kakao_static")["width"] == 360
    with pytest.raises(KeyError):
        core.load_preset("nope")
    assert cli.main(["check", str(tmp_path), "--preset", "nope"]) == 2
    assert cli.main(["check", str(tmp_path)]) == 1
    assert "수정 필요" in capsys.readouterr().out


def test_plan_and_draft():
    assert len(core.make_plan_table(32).splitlines()) == 33
    assert "하루" in core.proposal_draft("하루", "졸린 곰", "느긋함")
