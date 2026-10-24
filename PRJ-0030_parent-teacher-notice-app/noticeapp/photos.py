"""알림장 사진 처리: 위치 정보(EXIF) 제거, 크기 줄이기. JPEG/PNG만, 용량 제한."""
import os
from PIL import Image
from .store import NoticeError

MAX_BYTES = 8 * 1024 * 1024
MAX_SIDE = 1280


def clean_photo(src, dst_dir):
    if not os.path.isfile(src): raise NoticeError(f"사진 파일이 없습니다: {src}")
    if os.path.getsize(src) > MAX_BYTES: raise NoticeError(f"사진이 너무 큽니다(8MB 초과): {os.path.basename(src)}")
    try:
        im = Image.open(src); im.load()
    except Exception:
        raise NoticeError(f"사진으로 읽을 수 없습니다: {os.path.basename(src)}")
    if im.format not in ("JPEG", "PNG"): raise NoticeError(f"JPEG·PNG만 가능합니다: {os.path.basename(src)}")
    fmt = im.format
    im = im.convert("RGB") if fmt == "JPEG" else im
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    clean = Image.new(im.mode, im.size); clean.paste(im)            # 픽셀만 복사 → 메타데이터(위치·기기) 전부 사라짐
    os.makedirs(dst_dir, exist_ok=True)
    out = os.path.join(dst_dir, os.path.splitext(os.path.basename(src))[0] + (".jpg" if fmt == "JPEG" else ".png"))
    clean.save(out, fmt, **({"quality": 85} if fmt == "JPEG" else {}))
    return out
