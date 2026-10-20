"""글리프 SVG 폴더 점검: 빠진 글자, 파일명 규칙, 캔버스 이탈, 열린 경로."""
import os
import re
from .charset import required_chars
from .svgread import read_svg, points, SvgError

NAME = re.compile(r"^U\+([0-9A-Fa-f]{4,6})\.svg$")


def check_folder(folder, config, required=None):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"글리프 폴더가 없습니다: {folder}")
    required = required if required is not None else required_chars()
    req_cp = {ord(c) for c in required}
    canvas = config["canvas"]
    found, problems, warnings = {}, [], []
    for n in sorted(os.listdir(folder)):
        p = os.path.join(folder, n)
        if not os.path.isfile(p) or not n.lower().endswith(".svg"):
            continue
        m = NAME.match(n)
        if not m:
            problems.append((n, "파일명 규칙 위반 (예: U+AC00.svg, 16진수 대문자)"))
            continue
        cp = int(m.group(1), 16)
        if cp not in req_cp:
            warnings.append((n, "필수 목록에 없는 글자 (빌드는 됨)"))
        try:
            g = read_svg(p)
        except SvgError as e:
            problems.append((n, str(e))); continue
        if g["viewBox"] and tuple(g["viewBox"]) != (0, 0, canvas, canvas):
            problems.append((n, f"viewBox {g['viewBox']} (필요 0 0 {canvas} {canvas})"))
        if not g["subpaths"]:
            problems.append((n, "그려진 선이 없음")); continue
        if any(not (0 <= x <= canvas and 0 <= y <= canvas) for x, y in points(g["subpaths"])):
            problems.append((n, f"캔버스 {canvas}x{canvas} 밖으로 나간 점이 있음"))
        if any(not s["closed"] for s in g["subpaths"]):
            problems.append((n, "열린 경로가 있음 (Z로 닫아야 폰트가 됨)"))
        found[cp] = p
    missing = sorted(cp for cp in req_cp if cp not in found)
    return {"found": found, "problems": problems, "warnings": warnings, "missing": missing,
            "required": len(req_cp)}
