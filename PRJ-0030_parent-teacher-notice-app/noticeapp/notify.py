"""알림장 올리기·전달·읽음 확인. 문자/앱 푸시는 sender 함수를 꽂아서 보낸다(기본은 보내지 않는 시험용)."""
import datetime
import json
import re
from . import photos as P
from .store import NoticeError, class_id, new_token

MAX_TITLE, MAX_BODY = 60, 2000


def publish(c, class_name, title, body, photo_paths=(), kids_in_photos=(), out_dir="photos_clean", sender=None, link_base="https://example.invalid/n/", now=None):
    """알림장을 만들고 반 보호자 전원에게 전달 기록을 만든다. 사진에 나온 아이의 보호자가 사진 동의를 안 했으면 막는다."""
    title, body = title.strip(), body.strip()
    if not title or not body: raise NoticeError("제목과 내용이 필요합니다")
    if len(title) > MAX_TITLE: raise NoticeError(f"제목은 {MAX_TITLE}자 이하")
    if len(body) > MAX_BODY: raise NoticeError(f"내용은 {MAX_BODY}자 이하")
    cid = class_id(c, class_name)
    guardians = c.execute("SELECT * FROM guardians WHERE class_id=? AND active=1", (cid,)).fetchall()
    if not guardians: raise NoticeError("이 반에 등록된 보호자가 없습니다")
    if photo_paths:
        if not kids_in_photos: raise NoticeError("사진에 나온 아이 이름을 --kids로 알려 주세요(사진 동의 확인용)")
        blocked = []
        for kid in kids_in_photos:
            g = [x for x in guardians if x["child"] == kid]
            if not g: raise NoticeError(f"반에 없는 아이 이름입니다: {kid}")
            if not any(x["photo_ok"] for x in g): blocked.append(kid)
        if blocked: raise NoticeError("사진 공개 동의가 없는 아이가 있어 올릴 수 없습니다: " + ", ".join(blocked))
    clean = [P.clean_photo(p, out_dir) for p in photo_paths]          # 위치 정보 제거는 올리기 전에 항상 한다
    when = (now or datetime.datetime.now()).isoformat(timespec="seconds")
    cur = c.execute("INSERT INTO notices(class_id,title,body,photos,created) VALUES(?,?,?,?,?)", (cid, title, body, json.dumps(clean, ensure_ascii=False), when))
    nid, sent, failed = cur.lastrowid, 0, 0
    for g in guardians:
        tok = new_token()
        status = "대기"
        if sender:
            try:
                sender(g["phone"], f"[{class_name}] {title}\n{link_base}{tok}"); status = "전달"; sent += 1
            except Exception:
                status = "실패"; failed += 1
        c.execute("INSERT INTO deliveries(notice_id,guardian_id,token,status) VALUES(?,?,?,?)", (nid, g["id"], tok, status))
    c.commit()
    return {"notice_id": nid, "guardians": len(guardians), "sent": sent, "failed": failed, "photos": clean}


def open_by_token(c, token, now=None):
    """보호자가 링크를 열 때: 알림장 내용을 돌려주고 읽음으로 기록(처음 연 시각만 남김)."""
    r = c.execute("SELECT d.id, d.read_at, n.title, n.body, n.photos, n.created FROM deliveries d JOIN notices n ON n.id=d.notice_id WHERE d.token=?", (token,)).fetchone()
    if not r: raise NoticeError("잘못된 링크입니다")
    if not r["read_at"]:
        c.execute("UPDATE deliveries SET read_at=?, status='읽음' WHERE id=?", ((now or datetime.datetime.now()).isoformat(timespec="seconds"), r["id"])); c.commit()
    return {"title": r["title"], "body": r["body"], "photos": json.loads(r["photos"]), "created": r["created"]}


def retry_failed(c, notice_id, sender, link_base="https://example.invalid/n/"):
    rows = c.execute("SELECT d.id, d.token, g.phone, n.title FROM deliveries d JOIN guardians g ON g.id=d.guardian_id JOIN notices n ON n.id=d.notice_id WHERE d.notice_id=? AND d.status IN ('실패','대기')", (notice_id,)).fetchall()
    ok = 0
    for r in rows:
        try:
            sender(r["phone"], f"{r['title']}\n{link_base}{r['token']}"); c.execute("UPDATE deliveries SET status='전달' WHERE id=?", (r["id"],)); ok += 1
        except Exception:
            pass
    c.commit()
    return ok


def status(c, notice_id):
    rows = c.execute("SELECT g.child, g.name, d.status, d.read_at FROM deliveries d JOIN guardians g ON g.id=d.guardian_id WHERE d.notice_id=? ORDER BY g.child", (notice_id,)).fetchall()
    if not rows: raise NoticeError(f"없는 알림장입니다: {notice_id}")
    unread = [f"{r['child']}({r['name']})" for r in rows if r["status"] != "읽음"]
    return {"total": len(rows), "read": len(rows) - len(unread), "unread": unread, "failed": sum(1 for r in rows if r["status"] == "실패")}
