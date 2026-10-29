"""주문 제작(머그·포토북) 인쇄용 이미지 점검·변환. 인쇄 크기·해상도는 **예시 규격**이며 실제 제작사 규격은 확인하지 못했다."""
from PIL import Image, ImageOps

DPI = 300
PRODUCTS = {"mug_wrap": (200.0, 90.0), "photobook_page": (210.0, 210.0), "photobook_cover": (230.0, 230.0)}   # mm (예시)
OK_DPI, MIN_DPI, MAX_CROP = 250, 150, 0.20


class PrepError(ValueError):
    pass


def target_px(product):
    if product not in PRODUCTS: raise PrepError(f"알 수 없는 상품: {product} ({list(PRODUCTS)})")
    w, h = PRODUCTS[product]; return round(w / 25.4 * DPI), round(h / 25.4 * DPI)


def check(im, product, fit="cover"):
    tw, th = target_px(product); w, h = im.size
    scale = max(tw / w, th / h) if fit == "cover" else min(tw / w, th / h)
    eff = DPI / scale                                          # 이 사진을 목표 크기로 늘렸을 때의 실제 해상도(dpi)
    crop = 0.0
    if fit == "cover":
        shown = (tw / scale * th / scale) / (w * h); crop = round(1 - shown, 3)
    issues, level = [], "ok"
    if eff < MIN_DPI: level = "reject"; issues.append(f"사진이 너무 작아요(약 {eff:.0f}dpi, 최소 {MIN_DPI}dpi). 더 큰 사진이 필요해요")
    elif eff < OK_DPI: level = "warn"; issues.append(f"조금 흐리게 인쇄될 수 있어요(약 {eff:.0f}dpi)")
    if crop > MAX_CROP:
        level = "warn" if level == "ok" else level; issues.append(f"비율이 달라 사진의 {crop * 100:.0f}%가 잘려요")
    return {"level": level, "dpi": round(eff), "crop": crop, "issues": issues, "target": (tw, th)}


def prepare(im, product, fit="cover", bg=(255, 255, 255)):
    r = check(im, product, fit)
    if r["level"] == "reject": raise PrepError(r["issues"][0])
    im = ImageOps.exif_transpose(im).convert("RGB"); tw, th = r["target"]
    if fit == "cover": out = ImageOps.fit(im, (tw, th), Image.LANCZOS)
    else:
        out = Image.new("RGB", (tw, th), bg); c = ImageOps.contain(im, (tw, th), Image.LANCZOS); out.paste(c, ((tw - c.width) // 2, (th - c.height) // 2))
    return out, r
