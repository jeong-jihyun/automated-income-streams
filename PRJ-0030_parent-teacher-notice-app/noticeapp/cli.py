import argparse
import csv
import sys
from . import notify, store


def main(argv=None):
    p = argparse.ArgumentParser(prog="noticeapp", description="학부모-교사 알림장 (문자는 실제로 보내지 않는 시험용)")
    p.add_argument("--db", default="notices.db")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import-guardians", help="CSV: 반,아이,보호자,전화,사진동의(Y/N)"); s.add_argument("csv")
    s = sub.add_parser("publish"); s.add_argument("class_name"); s.add_argument("--title", required=True); s.add_argument("--body", required=True)
    s.add_argument("--photo", action="append", default=[]); s.add_argument("--kids", default=""); s.add_argument("--out", default="photos_clean")
    s = sub.add_parser("status"); s.add_argument("notice_id", type=int)
    a = p.parse_args(argv)
    try:
        c = store.connect(a.db)
        if a.cmd == "import-guardians":
            n = 0
            for i, r in enumerate(csv.reader(open(a.csv, encoding="utf-8-sig", newline="")), 1):
                if i == 1 and r and r[0] == "반": continue
                if len(r) < 5: print(f"[건너뜀] {i}행: 칸이 부족합니다"); continue
                try:
                    store.add_class(c, r[0]); store.add_guardian(c, r[0], r[1], r[2], r[3], r[4].strip().upper() == "Y"); n += 1
                except store.NoticeError as e:
                    print(f"[건너뜀] {i}행: {e}")
            print(f"[완료] 보호자 {n}명 등록")
        elif a.cmd == "publish":
            r = notify.publish(c, a.class_name, a.title, a.body, a.photo, [k.strip() for k in a.kids.split(",") if k.strip()], a.out, sender=None)
            print(f"[완료] 알림장 #{r['notice_id']} 등록, 보호자 {r['guardians']}명 전달 기록 생성 (실제 발송은 하지 않음)")
        else:
            r = notify.status(c, a.notice_id)
            print(f"읽음 {r['read']}/{r['total']}, 전달 실패 {r['failed']}, 아직 안 읽음: {', '.join(r['unread']) or '없음'}")
        return 0
    except (store.NoticeError, OSError) as e:
        print(f"[오류] {e}"); return 2
