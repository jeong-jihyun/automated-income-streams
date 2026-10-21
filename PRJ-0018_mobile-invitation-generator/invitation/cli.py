import argparse
from .build import build, load, InviteError


def main(argv=None):
    p = argparse.ArgumentParser(prog="invitation", description="모바일 초대장 만들기 (보내기·RSVP 서버는 없음)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check").add_argument("--config", required=True)
    b = sub.add_parser("build"); b.add_argument("--config", required=True); b.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        if a.cmd == "check":
            load(a.config); print("설정 확인 완료")
        else:
            r = build(a.config, a.out)
            print(f"[완료] index.html ({r['bytes'] // 1024}KB, 사진 {r['photos']}장), invitation.ics → {a.out}")
            print("올리는 곳(웹 호스팅)과 링크 공유는 직접 하세요. 참석 확인(RSVP) 기능은 없습니다.")
        return 0
    except InviteError as e:
        print(f"[오류] {e}")
        return 2
