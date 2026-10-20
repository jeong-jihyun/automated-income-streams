"""선화 이미지 점검: 형식, 크기(해상도), 흰 배경, 색 섞임, 회색 채움."""
import os
from PIL import Image

IMG_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}


def list_images(folder):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"이미지 폴더가 없습니다: {folder}")
    return sorted(n for n in os.listdir(folder) if os.path.splitext(n)[1].lower() in IMG_EXT)


def check_image(path, trim_in, specs):
    """문제 문자열 목록을 돌려준다. 빈 목록이면 합격."""
    problems = []
    try:
        with Image.open(path) as im:
            im.load()
            w, h = im.size
            need_w = trim_in[0] * specs["dpi"] * (1 - specs["size_tolerance_pct"] / 100)
            need_h = trim_in[1] * specs["dpi"] * (1 - specs["size_tolerance_pct"] / 100)
            if w < need_w or h < need_h:
                problems.append(f"너무 작음: {w}x{h}px (필요 약 {int(need_w)}x{int(need_h)}px 이상, {specs['dpi']}dpi 기준)")
            rgb = im.convert("RGB")
            small = rgb.copy(); small.thumbnail((400, 400))
            px = list(small.get_flattened_data()) if hasattr(small, 'get_flattened_data') else list(small.getdata())
            n = len(px)
            colored = sum(1 for r, g, b in px if max(r, g, b) - min(r, g, b) > 30) / n
            gray = sum(1 for r, g, b in px if 64 <= (r + g + b) / 3 <= 192 and max(r, g, b) - min(r, g, b) <= 30) / n
            corners = [small.getpixel(c) for c in ((0, 0), (small.width - 1, 0), (0, small.height - 1),
                                                   (small.width - 1, small.height - 1))]
            if min(sum(c) / 3 for c in corners) < specs["white_background_min_mean"]:
                problems.append("배경이 흰색이 아님 (모서리가 어둡거나 회색)")
            if colored > specs["colored_pixel_max_ratio"]:
                problems.append(f"색이 섞여 있음 (색 있는 부분 {colored:.1%}) — 흑백 선화가 필요")
            if gray > specs["gray_pixel_max_ratio"]:
                problems.append(f"회색 면이 많음 ({gray:.0%}) — 선만 있는 그림이 색칠하기 좋음")
    except Exception as e:
        problems.append(f"이미지를 열 수 없음: {type(e).__name__}")
    return problems


def check_folder(folder, trim_name, specs):
    from .specs import trim_size
    trim = trim_size(specs, trim_name)
    names = list_images(folder)
    ok, bad = [], {}
    for n in names:
        pr = check_image(os.path.join(folder, n), trim, specs)
        if pr:
            bad[n] = pr
        else:
            ok.append(n)
    return {"ok": ok, "bad": bad, "total": len(names)}
