"""아주 단순한 SVG 글리프 읽기: <path>(M L H V C Q Z 절대좌표)와 <rect>."""
import os
import re
import xml.etree.ElementTree as ET

MAX_BYTES = 1_000_000
TOKEN = re.compile(r"[A-Za-z]|-?\d*\.?\d+(?:[eE][-+]?\d+)?")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "Z": 0}


class SvgError(ValueError):
    pass


def parse_path(d):
    toks = TOKEN.findall(d)
    subs, cur, i, x, y = [], None, 0, 0.0, 0.0
    cmd = None
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            if t not in ARGS:
                raise SvgError(f"지원하지 않는 경로 명령 '{t}' (절대좌표 M L H V C Q Z 만 지원)")
            cmd = t; i += 1
            if cmd == "Z":
                if cur is not None:
                    cur["closed"] = True
                    x, y = cur["start"]
                continue
        if cmd is None:
            raise SvgError("경로가 명령 없이 시작함")
        n = ARGS[cmd]
        if cmd == "Z":
            raise SvgError("Z 뒤에 숫자가 있음")
        vals = toks[i:i + n]
        if len(vals) < n or any(v.isalpha() for v in vals):
            raise SvgError("경로 숫자가 모자람")
        v = [float(a) for a in vals]; i += n
        if cmd == "M":
            cur = {"closed": False, "start": (v[0], v[1]), "segs": [("M", v[0], v[1])]}
            subs.append(cur); x, y = v; cmd = "L"
        else:
            if cur is None:
                raise SvgError("M 없이 그리기 명령이 나옴")
            if cmd == "L": cur["segs"].append(("L", v[0], v[1])); x, y = v
            elif cmd == "H": cur["segs"].append(("L", v[0], y)); x = v[0]
            elif cmd == "V": cur["segs"].append(("L", x, v[0])); y = v[0]
            elif cmd == "C": cur["segs"].append(("C", *v)); x, y = v[4], v[5]
            elif cmd == "Q": cur["segs"].append(("Q", *v)); x, y = v[2], v[3]
    return subs


def read_svg(path):
    if os.path.getsize(path) > MAX_BYTES:
        raise SvgError("SVG 파일이 너무 큼 (1MB 초과)")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        raise SvgError(f"SVG 형식 오류: {e}")
    vb = root.get("viewBox")
    box = tuple(float(a) for a in vb.replace(",", " ").split()) if vb else None
    subs = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        if tag == "path" and el.get("d"):
            subs += parse_path(el.get("d"))
        elif tag == "rect":
            x, y, w, h = (float(el.get(k, 0)) for k in ("x", "y", "width", "height"))
            subs.append({"closed": True, "start": (x, y),
                         "segs": [("M", x, y), ("L", x + w, y), ("L", x + w, y + h), ("L", x, y + h)]})
    return {"viewBox": box, "subpaths": subs}


def points(subpaths):
    for s in subpaths:
        for seg in s["segs"]:
            v = seg[1:]
            for k in range(0, len(v), 2):
                yield v[k], v[k + 1]
