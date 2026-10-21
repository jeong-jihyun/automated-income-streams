"""이미지 검사: 이름 규칙, 크기, 스티커는 투명 배경."""
import os
import re
from PIL import Image


def _files(folder):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"폴더가 없습니다: {folder}")
    names = sorted(n for n in os.listdir(folder) if os.path.isfile(os.path.join(folder, n)))
    if not names:
        raise ValueError(f"폴더가 비어 있습니다: {folder}")
    return names


def check_stickers(folder, specs):
    st, pat = specs["sticker"], re.compile(specs["name_pattern"])
    ok, bad = [], {}
    for n in _files(folder):
        pr = []
        if not pat.match(n):
            pr.append("파일명 규칙 위반 (영문 소문자·숫자·하이픈)")
        elif not n.lower().endswith(".png"):
            pr.append("스티커는 투명 배경이 필요해서 PNG 여야 함")
        else:
            try:
                with Image.open(os.path.join(folder, n)) as im:
                    im.load()
                    w, h = im.size
                    if min(w, h) < st["min_source_px"]:
                        pr.append(f"너무 작음 ({w}x{h}, 최소 {st['min_source_px']}px)")
                    if im.mode not in ("RGBA", "LA", "PA") and "transparency" not in im.info:
                        pr.append("투명 배경이 아님 (알파 채널 없음)")
                    else:
                        a = im.convert("RGBA")
                        corners = [a.getpixel(c)[3] for c in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
                        if max(corners) > st["corner_alpha_max"]:
                            pr.append("모서리가 투명하지 않음 (배경이 채워져 있음)")
                        elif a.getchannel("A").getbbox() is None:
                            pr.append("그림이 없음 (전부 투명)")
            except Exception as e:
                pr.append(f"이미지를 열 수 없음: {type(e).__name__}")
        (bad.__setitem__(n, pr) if pr else ok.append(n))
    return {"ok": ok, "bad": bad}


def check_wallpapers(folder, specs):
    wp, pat = specs["wallpaper"], re.compile(specs["name_pattern"])
    ok, bad = [], {}
    for n in _files(folder):
        pr = []
        if not pat.match(n):
            pr.append("파일명 규칙 위반 (영문 소문자·숫자·하이픈)")
        else:
            try:
                with Image.open(os.path.join(folder, n)) as im:
                    im.load()
                    if min(im.size) < wp["min_short_side_px"]:
                        pr.append(f"너무 작음 ({im.size[0]}x{im.size[1]}, 짧은 변 최소 {wp['min_short_side_px']}px)")
            except Exception as e:
                pr.append(f"이미지를 열 수 없음: {type(e).__name__}")
        (bad.__setitem__(n, pr) if pr else ok.append(n))
    return {"ok": ok, "bad": bad}
