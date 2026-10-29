import json, os
import pytest
from PIL import Image
from printorder import prep, outbox
from printorder.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")
BIG, SMALL = Image.open(os.path.join(S, "photo_big.jpg")), Image.open(os.path.join(S, "photo_small.jpg"))


def test_target_px():
    assert prep.target_px("mug_wrap") == (2362, 1063) and prep.target_px("photobook_page") == (2480, 2480)
    with pytest.raises(prep.PrepError): prep.target_px("pillow")


def test_check_levels():
    assert prep.check(BIG, "photobook_page")["level"] in ("ok", "warn") and prep.check(SMALL, "mug_wrap")["level"] == "reject"
    x = prep.check(Image.new("RGB", (1800, 900)), "mug_wrap"); assert x["level"] == "warn" and any("흐리게" in i for i in x["issues"])
    assert prep.check(Image.new("RGB", (3000, 1400)), "mug_wrap")["level"] == "ok"


def test_crop_warning_and_contain():
    x = prep.check(Image.new("RGB", (3000, 3000)), "mug_wrap"); assert x["crop"] > 0.5 and any("잘려요" in i for i in x["issues"])
    assert prep.check(Image.new("RGB", (3000, 3000)), "mug_wrap", "contain")["crop"] == 0.0


def test_prepare_cover_and_contain():
    o, _ = prep.prepare(BIG, "mug_wrap"); assert o.size == (2362, 1063)
    c, _ = prep.prepare(BIG, "photobook_page", "contain", (255, 255, 255)); assert c.size == (2480, 2480) and c.getpixel((5, 5)) == (255, 255, 255)      # 위아래 여백
    with pytest.raises(prep.PrepError, match="너무 작아요"): prep.prepare(SMALL, "mug_wrap")


def test_exif_rotation_handled():
    im = Image.new("RGB", (2000, 3000)); ex = im.getexif(); ex[0x0112] = 6; im2 = Image.open(__import__("io").BytesIO((lambda b: (im.save(b, "JPEG", exif=ex.tobytes()), b.getvalue())[1])(__import__("io").BytesIO()))); o, _ = prep.prepare(im2, "photobook_page", "contain"); assert o.size == (2480, 2480)


def _order(tmp_path, oid="O1", qty=1):
    f = tmp_path / "p.png"; Image.new("RGB", (10, 10)).save(f); return {"order_id": oid, "product": "mug_wrap", "files": [str(f)], "quantity": qty}


def test_dispatch_once_idempotent(tmp_path):
    ob, sent = str(tmp_path / "ob.json"), []
    o = _order(tmp_path); assert outbox.dispatch(ob, o, sent.append) == "sent" and outbox.dispatch(ob, o, sent.append) == "already_sent" and len(sent) == 1


def test_failure_retry_then_manual(tmp_path):
    ob = str(tmp_path / "ob.json"); o = _order(tmp_path)
    def bad(_): raise ConnectionError("제작사 응답 없음")
    assert [outbox.dispatch(ob, o, bad) for _ in range(3)] == ["failed", "failed", "needs_manual"]
    assert outbox.dispatch(ob, o, lambda _: None) == "needs_manual" and outbox.load(ob)["O1"]["attempts"] == 3 and "제작사 응답 없음" in outbox.load(ob)["O1"]["error"]


def test_failure_then_success_resets(tmp_path):
    ob = str(tmp_path / "ob.json"); o = _order(tmp_path); n = {"i": 0}
    def flaky(_):
        n["i"] += 1
        if n["i"] < 2: raise TimeoutError("t")
    assert outbox.dispatch(ob, o, flaky) == "failed" and outbox.dispatch(ob, o, flaky) == "sent" and outbox.load(ob)["O1"]["error"] == ""


@pytest.mark.parametrize("patch,msg", [({"quantity": 0}, "quantity"), ({"quantity": 500}, "1~100"), ({"files": ["/nope.png"]}, "없어요"), ({"order_id": ""}, "order_id")])
def test_order_validation(tmp_path, patch, msg):
    with pytest.raises(outbox.OutboxError, match=msg): outbox.validate_order({**_order(tmp_path), **patch})


def test_corrupt_outbox(tmp_path):
    f = tmp_path / "ob.json"; f.write_text("{x"); 
    with pytest.raises(outbox.OutboxError): outbox.load(str(f))


def test_cli(tmp_path, capsys):
    assert main(["check", os.path.join(S, "photo_big.jpg"), "--product", "mug_wrap"]) == 0 and main(["check", os.path.join(S, "photo_small.jpg"), "--product", "mug_wrap"]) == 1
    out = str(tmp_path / "o.png"); assert main(["prepare", os.path.join(S, "photo_big.jpg"), out, "--product", "mug_wrap"]) == 0 and Image.open(out).info.get("dpi", (0,))[0] in (300, 299.9994, 300.0)
    o = _order(tmp_path); oj = tmp_path / "o.json"; oj.write_text(json.dumps({**o, "files": [out]}))
    assert main(["dispatch", str(oj), "--outbox", str(tmp_path / "ob.json"), "--vendor-dir", str(tmp_path / "v")]) == 0 and os.path.exists(tmp_path / "v" / "O1" / "order.json")
    assert main(["prepare", os.path.join(S, "photo_small.jpg"), out, "--product", "mug_wrap"]) == 2
