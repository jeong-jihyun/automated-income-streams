"""상품 사진 배경을 단색(흰색 등)으로 바꾸고 마켓 규격에 맞춰 저장한다. 배경이 단순한 사진만 처리하고, 복잡하면 '실패'로 알린다."""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

PRESETS = {"square_1000": (1000, 1000, 0.85), "market_800": (800, 800, 0.80), "wide_1200x900": (1200, 900, 0.85)}  # 예시 규격(실제 마켓 규격 미확인)


class PhotoError(ValueError):
    pass


def foreground_mask(im, tol=38, max_spread=30):
    a = np.asarray(im.convert("RGB")).astype(np.int16)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    spread = float(np.median(np.abs(border - bg).max(axis=1)))
    if spread > max_spread: raise PhotoError("배경이 단색이 아니에요(가장자리 색이 들쭉날쭉). 처리하지 않았어요")
    near = (np.abs(a - bg).max(axis=2) <= tol)
    lab, n = ndimage.label(near)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bgm = np.isin(lab, list(edge))
    bgm = ndimage.binary_opening(bgm, iterations=1)
    fg = ~bgm
    cover = fg.mean()
    if cover < 0.03: raise PhotoError("상품이 거의 안 보여요(배경과 색이 비슷해요)")
    if cover > 0.97: raise PhotoError("배경을 찾지 못했어요(사진 전체가 상품처럼 보여요)")
    return fg, tuple(int(x) for x in bg)


def process(im, preset="square_1000", color=(255, 255, 255), fix_light=True):
    if preset not in PRESETS: raise PhotoError(f"알 수 없는 규격: {preset}")
    W, H, fill = PRESETS[preset]
    if min(im.size) < 300: raise PhotoError("사진이 너무 작아요(짧은 변 300px 미만)")
    fg, _ = foreground_mask(im)
    ys, xs = np.where(fg)
    box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    rgb = im.convert("RGB")
    soft = Image.fromarray((fg * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(1.0))
    layer = Image.new("RGB", im.size, color); layer.paste(rgb, mask=soft)
    crop = layer.crop(box)
    if fix_light:
        a = np.asarray(crop).astype(np.float32); m = fg[box[1]:box[3], box[0]:box[2]]
        mean = a[m].mean() if m.any() else 128
        gain = float(np.clip(128 / max(mean, 1), 0.85, 1.2))
        a = np.where(m[..., None], np.clip(a * gain, 0, 255), a); crop = Image.fromarray(a.astype("uint8"))
    s = min(W * fill / crop.width, H * fill / crop.height)
    crop = crop.resize((max(1, round(crop.width * s)), max(1, round(crop.height * s))), Image.LANCZOS)
    out = Image.new("RGB", (W, H), color)
    out.paste(crop, ((W - crop.width) // 2, (H - crop.height) // 2))
    return out, {"preset": preset, "size": (W, H), "product_box": tuple(int(x) for x in box)}
