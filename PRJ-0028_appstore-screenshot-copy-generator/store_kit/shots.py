"""앱 화면 이미지 + 큰 글자 문구 → 스토어 스크린샷. 글자는 칸에 맞게 줄바꿈하고 크기를 줄인다."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageOps

FONT_CANDIDATES = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]


class ShotError(ValueError):
    pass


def find_font(path=None):
    for p in ([path] if path else []) + FONT_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    return None


def load_font(path, size):
    if not path:
        return ImageFont.load_default()
    return ImageFont.truetype(path, size, index=1) if path.endswith(".ttc") else ImageFont.truetype(path, size)


def hex_rgb(h):
    h = h.lstrip("#")
    if len(h) != 6:
        raise ShotError(f"색은 #RRGGBB 형식이어야 합니다: {h}")
    try:
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        raise ShotError(f"색은 #RRGGBB 형식이어야 합니다: {h}")


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) > max_w and cur:
            lines.append(cur); cur = ch.lstrip()
        else:
            cur += ch
    return lines + ([cur] if cur else [])


def fit_text(draw, text, font_path, max_w, max_h, start=120, min_size=36):
    """칸 안에 들어가는 가장 큰 글자 크기를 찾는다. 끝내 안 들어가면 오류."""
    size = start
    while size >= min_size:
        f = load_font(font_path, size); lines = wrap(draw, text, f, max_w)
        if len(lines) * size * 1.25 <= max_h:
            return f, lines, size
        size -= 4
    raise ShotError(f"문구가 너무 길어 칸에 들어가지 않습니다: {text[:20]}…")


def make_shot(app_img_path, headline, bg_hex, size, font_path=None):
    W, H = size
    try:
        app = Image.open(app_img_path).convert("RGB")
    except (FileNotFoundError, OSError):
        raise ShotError(f"이미지를 열 수 없습니다: {app_img_path}")
    canvas = Image.new("RGB", size, hex_rgb(bg_hex)); d = ImageDraw.Draw(canvas)
    margin = int(W * 0.08); head_h = int(H * 0.18)
    f, lines, fs = fit_text(d, headline, font_path, W - 2 * margin, head_h)
    y = margin
    for ln in lines:
        d.text((W // 2, y), ln, font=f, fill="white", anchor="ma"); y += int(fs * 1.25)
    top = margin + head_h + margin // 2
    box_w, box_h = W - 2 * margin, H - top - margin
    fitted = ImageOps.contain(app, (box_w, box_h))
    mask = Image.new("L", fitted.size, 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, *fitted.size), radius=int(W * 0.04), fill=255)
    canvas.paste(fitted, ((W - fitted.width) // 2, top), mask)
    return canvas
