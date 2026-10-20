"""판매 페이지용 미리보기 모음 이미지(컨택트 시트)."""
import math
import os
from PIL import Image, ImageDraw


def contact_sheet(folder, names, out_path, specs):
    cs = specs["contact_sheet"]
    cols, (cw, ch), gap = cs["columns"], cs["cell"], cs["gap"]
    label_h = 20
    rows = math.ceil(len(names) / cols)
    W = cols * cw + (cols + 1) * gap
    H = rows * (ch + label_h) + (rows + 1) * gap
    sheet = Image.new("RGB", (W, H), (245, 245, 245))
    d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        r, c = divmod(i, cols)
        x = gap + c * (cw + gap)
        y = gap + r * (ch + label_h + gap)
        with Image.open(os.path.join(folder, n)) as im:
            im = im.convert("RGB"); im.thumbnail((cw, ch))
            sheet.paste(im, (x + (cw - im.width) // 2, y + (ch - im.height) // 2))
        d.text((x, y + ch + 3), n, fill=(60, 60, 60))
    sheet.save(out_path)
    return {"cols": cols, "rows": rows, "size": sheet.size}
