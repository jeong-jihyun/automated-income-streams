import argparse
import os
from PIL import Image
from . import make
from .bg import PhotoError


def main(argv=None):
    p = argparse.ArgumentParser(prog="profilephoto", description="셀카로 이력서·SNS용 프로필 사진 만들기 (얼굴 보정·모양 변경 없음)")
    p.add_argument("photo"); p.add_argument("--preset", default="linkedin", choices=list(make.PRESETS)); p.add_argument("--color", default="white", choices=list(make.COLORS))
    p.add_argument("--face", help="얼굴 상자 x,y,가로,세로(픽셀)"); p.add_argument("--keep-bg", action="store_true"); p.add_argument("--out", required=True)
    a = p.parse_args(argv)
    try:
        face = tuple(float(v) for v in a.face.split(",")) if a.face else None
        if face and len(face) != 4: raise PhotoError("--face는 x,y,가로,세로 네 숫자")
        im = Image.open(a.photo); im.load()
        out, notes = make.make(im, a.preset, face, a.color, not a.keep_bg)
        out.save(a.out, dpi=(300, 300)); print(f"[완료] {a.out} ({out.size[0]}x{out.size[1]}) — {make.PRESETS[a.preset][3]}")
        for n in notes: print("-", n)
        return 0
    except (PhotoError, ValueError, OSError) as e:
        print(f"[오류] {e}"); return 2
