"""스타일 설정 JSON 읽기와 점검."""
import json
import os
import re
import shutil
import subprocess

COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
LIMITS = {"size": (10, 200), "outline": (0, 20), "shadow": (0, 20), "alignment": (1, 9),
          "margin_v": (0, 400), "fade_in_ms": (0, 2000), "fade_out_ms": (0, 2000)}
DEFAULTS = {"outline_color": "#000000", "outline": 0, "shadow": 0, "bold": False, "alignment": 2,
            "margin_v": 40, "fade_in_ms": 0, "fade_out_ms": 0, "sample_text": "샘플 자막입니다"}


def load(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"설정 파일이 없습니다: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"설정 JSON 형식 오류: {e}")
    for k in ("pack_name", "styles"):
        if k not in cfg:
            raise ValueError(f"설정에 '{k}' 가 없습니다")
    if not cfg["styles"]:
        raise ValueError("styles 가 비어 있습니다")
    cfg.setdefault("theme", "")
    cfg.setdefault("resolution", [1280, 720])
    cfg.setdefault("background", "#333333")
    cfg.setdefault("fonts", [])
    for s in cfg["styles"]:
        for k, v in DEFAULTS.items():
            s.setdefault(k, v)
    return cfg


def installed_fonts():
    """설치된 글꼴 이름 집합. fc-list 가 없으면 None (확인 불가)."""
    if shutil.which("fc-list") is None:
        return None
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    names = set()
    for line in out.splitlines():
        for n in line.split(","):
            names.add(n.strip().lower())
    return names


def validate(cfg, fonts=None):
    """(문제 목록, 경고 목록) 반환."""
    problems, warnings = [], []
    w, h = cfg["resolution"]
    if not (isinstance(w, int) and isinstance(h, int) and w >= 320 and h >= 240):
        problems.append("resolution 은 [가로, 세로] 정수 (최소 320x240)")
    if not COLOR.match(cfg["background"]):
        problems.append("background 색은 #RRGGBB 형식")
    listed = {f["name"].lower(): f for f in cfg["fonts"]}
    fonts = installed_fonts() if fonts is None else fonts
    seen = set()
    for s in cfg["styles"]:
        sid = s.get("id", "")
        tag = f"[{sid or '?'}]"
        if not ID.match(sid):
            problems.append(f"{tag} id 는 영문 소문자·숫자·하이픈")
        elif sid in seen:
            problems.append(f"{tag} id 가 겹침")
        seen.add(sid)
        for key in ("color", "outline_color"):
            if not COLOR.match(str(s.get(key, ""))):
                problems.append(f"{tag} {key} 색 값 오류: {s.get(key)!r} (예: #FFFFFF)")
        for key, (lo, hi) in LIMITS.items():
            v = s.get(key)
            if not isinstance(v, (int, float)) or isinstance(v, bool) or not (lo <= v <= hi):
                problems.append(f"{tag} {key} 은 {lo}~{hi} 사이 숫자 (현재 {v!r})")
        font = s.get("font", "")
        if not font:
            problems.append(f"{tag} font 가 비어 있음")
        else:
            if fonts is not None and font.lower() not in fonts:
                problems.append(f"{tag} 글꼴 '{font}' 이(가) 이 컴퓨터에 설치되어 있지 않음")
            if font.lower() not in listed:
                warnings.append(f"{tag} 글꼴 '{font}' 의 라이선스 정보가 fonts 목록에 없음")
            elif listed[font.lower()].get("license", "unknown") in ("", "unknown"):
                warnings.append(f"{tag} 글꼴 '{font}' 의 라이선스가 'unknown'")
    if fonts is None:
        warnings.append("fc-list 가 없어 글꼴 설치 여부를 확인하지 못했습니다")
    return problems, warnings
