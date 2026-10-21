"""스티커 가공(여백 자르기, 흰 테두리), 시트 배치, 배경화면 리사이즈."""
import os
from PIL import Image, ImageFilter, ImageOps


def make_sticker(src, dst, st):
    with Image.open(src) as im:
        im = im.convert("RGBA")
    box = im.getchannel("A").getbbox()
    if box is None:
        raise ValueError(f"그림이 없는 이미지: {os.path.basename(src)}")
    im = im.crop(box)
    inner = st["max_px"] - 2 * (st["border_px"] + st["padding_px"])
    im.thumbnail((inner, inner), Image.LANCZOS)
    b, pad = st["border_px"], st["padding_px"]
    canvas = Image.new("RGBA", (im.width + 2 * (b + pad), im.height + 2 * (b + pad)), (0, 0, 0, 0))
    canvas.paste(im, (b + pad, b + pad))
    alpha = canvas.getchannel("A")
    k = 2 * b + 1
    grown = alpha.filter(ImageFilter.MaxFilter(k if k % 2 else k + 1))
    outline = Image.new("RGBA", canvas.size, (255, 255, 255, 255))
    outline.putalpha(grown)
    out = Image.alpha_composite(outline, canvas)
    out.save(dst)
    return out.size


def pack_sheets(sizes, sheet_cfg):
    """선반(shelf) 방식 배치. sizes: [(이름, w, h)] → [[(이름, x, y, w, h), ...] (시트별)]"""
    SW, SH = sheet_cfg["size"]; m, gap = sheet_cfg["margin"], sheet_cfg["gap"]
    items = sorted(sizes, key=lambda t: (-t[2], t[0]))
    for n, w, h in items:
        if w > SW - 2 * m or h > SH - 2 * m:
            raise ValueError(f"스티커 '{n}' ({w}x{h}) 가 시트({SW}x{SH}, 여백 {m})보다 큼")
    sheets, cur = [], []
    x, y, row_h = m, m, 0
    for n, w, h in items:
        if x + w > SW - m:  # 줄 바꿈
            x, y, row_h = m, y + row_h + gap, 0
        if y + h > SH - m:  # 새 시트
            sheets.append(cur); cur = []
            x, y, row_h = m, m, 0
        cur.append((n, x, y, w, h))
        x += w + gap
        row_h = max(row_h, h)
    if cur:
        sheets.append(cur)
    return sheets


def render_sheet(placements, sticker_dir, sheet_cfg, out_path):
    SW, SH = sheet_cfg["size"]
    sheet = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
    for n, x, y, w, h in placements:
        with Image.open(os.path.join(sticker_dir, n)) as im:
            sheet.alpha_composite(im.convert("RGBA"), (x, y))
    sheet.save(out_path)
    return (SW, SH)


def make_wallpapers(src, out_dir, base, sizes, quality):
    os.makedirs(out_dir, exist_ok=True)
    made = []
    with Image.open(src) as im:
        im = im.convert("RGB")
        for w, h in sizes:
            p = os.path.join(out_dir, f"{base}_{w}x{h}.jpg")
            ImageOps.fit(im, (w, h), Image.LANCZOS).save(p, quality=quality)
            made.append(p)
    return made
