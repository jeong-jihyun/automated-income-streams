import json
import os
import re
from datetime import date
import pytest
from PIL import Image
from invitation import build as B
from invitation.cli import main

D = os.path.join(os.path.dirname(__file__), "..", "sample")
CFG = os.path.join(D, "event.json")


def mk(tmp_path, **ch):
    ev = json.load(open(CFG, encoding="utf-8")); ev.update(ch)
    for n in ("photo1.jpg", "photo2.jpg"):
        Image.open(os.path.join(D, n)).save(tmp_path / n)
    p = tmp_path / "e.json"; p.write_text(json.dumps(ev, ensure_ascii=False), encoding="utf-8"); return str(p)


def test_build_outputs(tmp_path):
    out = tmp_path / "o"
    r = B.build(mk(tmp_path), str(out), today=date(2031, 5, 1))
    h = (out / "index.html").read_text(encoding="utf-8")
    assert h.count("data:image/jpeg;base64,") == 2 and 'name="viewport"' in h
    assert "D-9" in h and "철수 ♥ 영희" in h and "tel:01000000000" in h and "map.naver.com" in h
    assert "소중한 분들을 초대합니다.<br>함께" in h


def test_photo_resized_and_rotated(tmp_path):
    im = Image.new("RGB", (3000, 2000)); p = tmp_path / "big.jpg"; im.save(p)
    uri = B.photo_data_uri(str(p))
    import base64, io
    out = Image.open(io.BytesIO(base64.b64decode(uri.split(",")[1])))
    assert max(out.size) == 900
    with pytest.raises(B.InviteError, match="사진을 열 수"): B.photo_data_uri(str(tmp_path / "none.jpg"))


def test_dday():
    assert B.dday_text(date(2031, 5, 10), date(2031, 5, 10)) == "오늘입니다"
    assert B.dday_text(date(2031, 5, 10), date(2031, 5, 9)) == "D-1"
    assert B.dday_text(date(2031, 5, 10), date(2031, 5, 12)) == "2일 지났습니다"


def test_html_escaped(tmp_path):
    cfg = mk(tmp_path, title="<script>x</script>", greeting="<b>안녕</b>")
    ev = B.load(cfg); h = B.build_html(ev, str(tmp_path), date(2031, 1, 1))
    assert "<script>" not in h and "&lt;script&gt;" in h and "&lt;b&gt;안녕" in h


def test_ics_format(tmp_path):
    ev = B.load(mk(tmp_path, place="홀, 3층; 별관"))
    ics = B.make_ics(ev)
    assert "DTSTART:20310510T133000" in ics and "DTEND:20310510T153000" in ics and "홀\\, 3층\\; 별관" in ics
    assert ics.startswith("BEGIN:VCALENDAR") and ics.rstrip().endswith("END:VCALENDAR") and "\r\n" in ics


@pytest.mark.parametrize("ch,msg", [({"date": "2031-02-30"}, "형식"), ({"time": "25:00"}, "형식"), ({"title": " "}, "title"),
                                    ({"theme": "x"}, "theme"), ({"photos": ["a.jpg"] * 9}, "최대 8장"),
                                    ({"contacts": [{"label": "a", "tel": "abc"}]}, "전화번호")])
def test_validation(tmp_path, ch, msg):
    with pytest.raises(B.InviteError, match=msg): B.load(mk(tmp_path, **ch))


def test_load_errors(tmp_path):
    with pytest.raises(B.InviteError, match="없습니다"): B.load(str(tmp_path / "x.json"))
    (tmp_path / "b.json").write_text("{", encoding="utf-8")
    with pytest.raises(B.InviteError, match="JSON"): B.load(str(tmp_path / "b.json"))


def test_cli(tmp_path):
    assert main(["check", "--config", mk(tmp_path)]) == 0
    assert main(["build", "--config", mk(tmp_path), "--out", str(tmp_path / "o")]) == 0
    assert os.path.exists(tmp_path / "o" / "invitation.ics")
    assert main(["build", "--config", str(tmp_path / "no.json"), "--out", str(tmp_path / "o2")]) == 2
