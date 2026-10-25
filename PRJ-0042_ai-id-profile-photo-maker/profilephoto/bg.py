"""배경 바꾸기(AI 아님): 사진 가장자리 색을 배경으로 보고, 가장자리와 이어진 비슷한 색을 지운다. 단색에 가까운 배경에서만 잘 된다."""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage


class PhotoError(ValueError):
    pass


def border_pixels(a):
    return np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])


def detect(im, tol=40, max_spread=35):
    """(배경색, 마스크(True=사람/물건), 배경이 단순한가) 반환."""
    a = np.asarray(im.convert("RGB")).astype(int)
    b = border_pixels(a); med = np.median(b, axis=0)
    spread = float(np.median(np.abs(b - med).sum(axis=1)))
    dist = np.abs(a - med).sum(axis=2)
    bgish = dist <= tol
    lab, n = ndimage.label(bgish)
    border_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    background = np.isin(lab, list(border_labels)) if border_labels else np.zeros_like(bgish)
    fg = ~background
    fg = ndimage.binary_opening(fg, iterations=1)
    return tuple(int(x) for x in med), fg, spread <= max_spread


def replace(im, color, tol=40, feather=1.2):
    """배경을 color로 바꾼 RGB 이미지와 정보를 돌려준다. 배경이 복잡하면 ok=False (바꾸지 않고 원본 반환)."""
    med, fg, simple = detect(im, tol)
    cover = float(fg.mean())
    if not simple: return im.convert("RGB"), {"ok": False, "reason": "배경이 복잡해서 안전하게 바꿀 수 없어요(단색에 가까운 벽 앞에서 찍어 주세요)", "foreground": cover}
    if cover < 0.05 or cover > 0.95: return im.convert("RGB"), {"ok": False, "reason": "사람/물건을 구분하지 못했어요", "foreground": cover}
    alpha = Image.fromarray((fg * 255).astype("uint8")).filter(ImageFilter.GaussianBlur(feather))
    bg = Image.new("RGB", im.size, color)
    return Image.composite(im.convert("RGB"), bg, alpha), {"ok": True, "reason": "", "foreground": cover}
