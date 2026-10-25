"""프로필 사진 만들기: 점검 → 얼굴 중심 자르기 → 배경색 → 밝기 보정 → 규격 크기. 얼굴·피부를 고치거나 모양을 바꾸지 않는다."""
from PIL import Image, ImageFilter, ImageOps, ImageStat
from . import bg
from .bg import PhotoError

PRESETS = {  # 이름: (가로px, 세로px, 머리 높이 비율, 설명)
    "linkedin": (800, 800, 0.45, "SNS·링크드인용 정사각형"),
    "resume_3x4": (354, 472, 0.55, "이력서 3×4cm (300dpi)"),
    "id_35x45": (413, 531, 0.60, "3.5×4.5cm (300dpi) — 연습용 규격, 여권·신분증 제출용 아님"),
}
COLORS = {"white": (255, 255, 255), "gray": (235, 235, 235), "blue": (205, 225, 245)}
MIN_SIDE = 600


def check(im):
    probs = []
    if min(im.size) < MIN_SIDE: probs.append(f"사진이 작아요(짧은 변 {MIN_SIDE}px 이상 권장)")
    g = im.convert("L")
    if ImageStat.Stat(g).mean[0] < 60: probs.append("너무 어두워요")
    if ImageStat.Stat(g).mean[0] > 220: probs.append("너무 밝아요")
    if ImageStat.Stat(g.filter(ImageFilter.FIND_EDGES)).var[0] < 15: probs.append("흐리거나 윤곽이 없어요")
    return probs


def crop_box(size, face, aspect, head_ratio):
    """얼굴 상자(x,y,w,h)를 기준으로, 머리가 세로의 head_ratio가 되게 자를 영역(left, top, right, bottom). 사진 밖이면 좌표가 음수/초과(→ 배경색으로 채움)."""
    x, y, w, h = face
    ch = h / head_ratio; cw = ch * aspect
    cx = x + w / 2; cy = y + h / 2 + ch * 0.08            # 얼굴 중심보다 살짝 아래를 중심으로(어깨가 보이게)
    return (round(cx - cw / 2), round(cy - ch / 2), round(cx + cw / 2), round(cy + ch / 2))


def normalize_light(im, lo=0.85, hi=1.2):
    """밝기만 살짝 맞춘다(색은 그대로): 전체 밝기가 128에서 멀면 모든 색에 같은 배수를 곱한다. 배수는 0.85~1.2로 제한."""
    m = ImageStat.Stat(im.convert("L")).mean[0]
    gain = max(lo, min(hi, 128 / m)) if m > 0 else 1.0
    return im.point(lambda v: min(255, int(v * gain))), gain


def make(im, preset, face=None, color="white", change_bg=True):
    if preset not in PRESETS: raise PhotoError("규격은 " + "/".join(PRESETS))
    if color not in COLORS: raise PhotoError("배경색은 " + "/".join(COLORS))
    W, H, ratio, _ = PRESETS[preset]; notes = check(im); im = ImageOps.exif_transpose(im).convert("RGB")
    if face is None:
        face = (im.width * 0.3, im.height * 0.12, im.width * 0.4, im.height * 0.4); notes.append("얼굴 위치를 안 알려 주어 가운데 위쪽으로 추정했어요(--face x,y,가로,세로 권장)")
    else:
        x, y, w, h = face
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > im.width or y + h > im.height: raise PhotoError("얼굴 상자가 사진 밖이에요")
    box = crop_box(im.size, face, W / H, ratio)
    pad = box[0] < 0 or box[1] < 0 or box[2] > im.width or box[3] > im.height
    canvas = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), COLORS[color]); canvas.paste(im, (-box[0], -box[1]))
    canvas, _ = normalize_light(canvas)
    if pad:
        notes.append("사진 가장자리가 모자라 배경색으로 채웠어요(머리/어깨 여유가 부족한 사진). 배경은 바꾸지 않았어요")
    elif change_bg:
        out, info = bg.replace(canvas, COLORS[color])
        if info["ok"]: canvas = out
        else: notes.append("배경은 바꾸지 않았어요: " + info["reason"])
    return canvas.resize((W, H), Image.LANCZOS), notes
