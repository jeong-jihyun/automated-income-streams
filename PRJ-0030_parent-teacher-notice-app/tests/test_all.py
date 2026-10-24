import os
import pytest
from PIL import Image
from noticeapp import notify, photos, store
from noticeapp.cli import main

S = os.path.join(os.path.dirname(__file__), "..", "sample")


@pytest.fixture
def db(tmp_path):
    c = store.connect(str(tmp_path / "n.db")); store.add_class(c, "해님반")
    store.add_guardian(c, "해님반", "김하늘", "김엄마", "010-1111-2222", True)
    store.add_guardian(c, "해님반", "이바다", "이아빠", "010-3333-4444", False)
    store.add_guardian(c, "해님반", "박구름", "박엄마", "010-5555-6666", True)
    return c


def exif_photo(path):
    im = Image.new("RGB", (2000, 1000), (10, 20, 30)); ex = Image.Exif(); ex[0x010F] = "SecretPhone"; ex[0x8825] = {1: "N", 2: (37.0, 30.0, 0.0)}
    im.save(path, "JPEG", exif=ex.tobytes()); return str(path)


def test_photo_strips_metadata_and_resizes(tmp_path):
    src = exif_photo(tmp_path / "a.jpg"); assert Image.open(src).getexif().get(0x010F) == "SecretPhone"
    out = photos.clean_photo(src, str(tmp_path / "o")); im = Image.open(out)
    assert not dict(im.getexif()) and max(im.size) == 1280


def test_photo_rejects_bad_files(tmp_path):
    (tmp_path / "x.jpg").write_text("not an image")
    with pytest.raises(store.NoticeError, match="읽을 수 없"): photos.clean_photo(str(tmp_path / "x.jpg"), str(tmp_path))
    Image.new("RGB", (5, 5)).save(tmp_path / "g.gif")
    with pytest.raises(store.NoticeError, match="JPEG·PNG"): photos.clean_photo(str(tmp_path / "g.gif"), str(tmp_path))
    with pytest.raises(store.NoticeError, match="없습니다"): photos.clean_photo(str(tmp_path / "none.jpg"), str(tmp_path))


def test_publish_sends_to_all_with_personal_links(db):
    sent = []
    r = notify.publish(db, "해님반", "소풍 안내", "금요일 소풍입니다", sender=lambda ph, msg: sent.append((ph, msg)))
    assert r["sent"] == 3 and len({m.split("/n/")[1] for _, m in sent}) == 3 and sent[0][0] == "01011112222"


def test_photo_consent_blocks_and_requires_kids(db, tmp_path):
    p = exif_photo(tmp_path / "a.jpg")
    with pytest.raises(store.NoticeError, match="동의가 없는 아이: 이바다|동의가 없는 아이가 있어.*이바다"): notify.publish(db, "해님반", "t", "b", [p], ["김하늘", "이바다"])
    with pytest.raises(store.NoticeError, match="--kids"): notify.publish(db, "해님반", "t", "b", [p], [])
    with pytest.raises(store.NoticeError, match="반에 없는"): notify.publish(db, "해님반", "t", "b", [p], ["최없음"])
    assert db.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0                # 막히면 아무것도 저장되지 않음
    r = notify.publish(db, "해님반", "t", "b", [p], ["김하늘", "박구름"], out_dir=str(tmp_path / "o"))
    assert not dict(Image.open(r["photos"][0]).getexif())


def test_read_receipt_and_status(db):
    notify.publish(db, "해님반", "공지", "내용")
    tok = db.execute("SELECT token FROM deliveries ORDER BY id LIMIT 1").fetchone()[0]
    v = notify.open_by_token(db, tok, now=__import__("datetime").datetime(2026, 10, 24, 9, 0)); assert v["title"] == "공지"
    notify.open_by_token(db, tok, now=__import__("datetime").datetime(2026, 10, 25, 9, 0))      # 두 번째 열기는 시각을 바꾸지 않음
    assert db.execute("SELECT read_at FROM deliveries WHERE token=?", (tok,)).fetchone()[0].startswith("2026-10-24")
    st = notify.status(db, 1); assert st["read"] == 1 and st["total"] == 3 and len(st["unread"]) == 2
    with pytest.raises(store.NoticeError, match="잘못된 링크"): notify.open_by_token(db, "bad")


def test_failed_send_and_retry(db):
    def flaky(ph, msg):
        if ph.endswith("4444"): raise RuntimeError("fail")
    r = notify.publish(db, "해님반", "공지", "내용", sender=flaky)
    assert r["sent"] == 2 and r["failed"] == 1 and notify.status(db, 1)["failed"] == 1
    assert notify.retry_failed(db, 1, lambda *a: None) == 1 and notify.status(db, 1)["failed"] == 0


def test_validation(db):
    with pytest.raises(store.NoticeError, match="제목과 내용"): notify.publish(db, "해님반", " ", "b")
    with pytest.raises(store.NoticeError, match="2000"): notify.publish(db, "해님반", "t", "가" * 2001)
    with pytest.raises(store.NoticeError, match="없는 반"): notify.publish(db, "달님반", "t", "b")
    with pytest.raises(store.NoticeError, match="전화번호"): store.add_guardian(db, "해님반", "x", "y", "123")
    with pytest.raises(store.NoticeError, match="이미 등록"): store.add_guardian(db, "해님반", "김하늘", "김엄마", "01011112222")
    store.add_class(db, "빈반")
    with pytest.raises(store.NoticeError, match="보호자가 없"): notify.publish(db, "빈반", "t", "b")


def test_cli(tmp_path, capsys):
    d = str(tmp_path / "c.db")
    assert main(["--db", d, "import-guardians", os.path.join(S, "guardians.csv")]) == 0 and "3명" in capsys.readouterr().out
    assert main(["--db", d, "publish", "해님반", "--title", "안내", "--body", "내용", "--photo", os.path.join(S, "photo1.jpg"), "--kids", "이바다", "--out", str(tmp_path / "o")]) == 2
    assert main(["--db", d, "publish", "해님반", "--title", "안내", "--body", "내용", "--photo", os.path.join(S, "photo1.jpg"), "--kids", "김하늘,박구름", "--out", str(tmp_path / "o")]) == 0
    assert main(["--db", d, "status", "1"]) == 0 and "읽음 0/3" in capsys.readouterr().out
