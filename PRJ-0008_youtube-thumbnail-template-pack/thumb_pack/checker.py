"""규격 점검: 파일명 규칙, 형식, 크기(px), 용량."""
import os
import re
from PIL import Image


def check_file(path, specs):
    name = os.path.basename(path)
    problems = []
    m = re.match(specs["name_pattern"], name)
    if not m:
        return ["파일명 규칙 위반 (예: thumb_game-01.png, art_game-01.jpg — 영문 소문자·숫자·하이픈)"]
    kind = specs["kinds"][m.group(1)]
    size_mb = os.path.getsize(path) / 1024 / 1024
    try:
        with Image.open(path) as im:
            im.load()
            if im.format not in specs["allowed_formats"]:
                problems.append(f"형식 {im.format} 허용 안 됨")
            if list(im.size) != kind["size"]:
                problems.append(f"크기 {im.size[0]}x{im.size[1]} (필요 {kind['size'][0]}x{kind['size'][1]})")
    except Exception as e:
        return [f"이미지를 열 수 없음: {type(e).__name__}"]
    if size_mb > kind["max_mb"]:
        problems.append(f"용량 {size_mb:.1f}MB (최대 {kind['max_mb']}MB)")
    return problems


def check_folder(folder, specs):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"폴더가 없습니다: {folder}")
    names = sorted(n for n in os.listdir(folder) if os.path.isfile(os.path.join(folder, n)))
    if not names:
        raise ValueError("폴더가 비어 있습니다")
    ok, bad = [], {}
    for n in names:
        pr = check_file(os.path.join(folder, n), specs)
        (bad.__setitem__(n, pr) if pr else ok.append(n))
    return {"ok": ok, "bad": bad, "total": len(names)}
