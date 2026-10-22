"""이미지 → 글자. 컴퓨터에 설치된 tesseract 프로그램을 부른다(없으면 안내). 한글은 'kor' 언어 데이터가 설치되어 있어야 한다."""
import shutil
import subprocess
from PIL import Image, ImageOps


class OcrError(RuntimeError):
    pass


def available_langs():
    exe = shutil.which("tesseract")
    if not exe:
        return None
    out = subprocess.run([exe, "--list-langs"], capture_output=True, text=True).stdout.splitlines()[1:]
    return {l.strip() for l in out if l.strip()}


def preprocess(path, out_path, max_side=2000):
    """흑백 + 대비 자동 조정 + 너무 작으면 키우기(글자 인식률을 높이기 위한 기본 손질)."""
    try:
        im = ImageOps.exif_transpose(Image.open(path)).convert("L")
    except (FileNotFoundError, OSError):
        raise OcrError(f"이미지를 열 수 없습니다: {path}")
    im = ImageOps.autocontrast(im)
    if max(im.size) < 1000:
        k = 1000 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)))
    im.thumbnail((max_side, max_side))
    im.save(out_path)
    return out_path


def read_text(path, lang="kor+eng", tmp_dir="."):
    langs = available_langs()
    if langs is None:
        raise OcrError("tesseract 프로그램이 설치되어 있지 않습니다 (설치 후 다시 실행하세요)")
    want = lang.split("+")
    missing = [l for l in want if l not in langs]
    if missing:
        raise OcrError(f"언어 데이터가 없습니다: {', '.join(missing)} (설치된 것: {', '.join(sorted(langs))})")
    import os
    pre = preprocess(path, os.path.join(tmp_dir, "_pre.png"))
    r = subprocess.run([shutil.which("tesseract"), pre, "stdout", "-l", lang, "--psm", "6"], capture_output=True, text=True)
    if r.returncode != 0:
        raise OcrError(f"글자 인식 실패: {r.stderr.strip()[:200]}")
    return r.stdout
