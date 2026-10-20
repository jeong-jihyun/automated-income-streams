"""아이콘 점검: 파일명, 크기, 투명 배경, 중복, 스타일(색 범위)."""
import hashlib
import os
import re
from collections import Counter
from PIL import Image


def list_pngs(folder):
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"그림 폴더가 없습니다: {folder}")
    names = sorted(n for n in os.listdir(folder) if os.path.isfile(os.path.join(folder, n)))
    if not names:
        raise ValueError("그림 폴더가 비어 있습니다")
    return names


def has_alpha(im):
    return im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info


def ahash(im, n=8):
    """평균 해시. 투명 부분은 흰색으로 합쳐서 계산한다."""
    rgba = im.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    g = Image.alpha_composite(bg, rgba).convert("L").resize((n, n), Image.LANCZOS)
    px = list(g.get_flattened_data()) if hasattr(g, "get_flattened_data") else list(g.getdata())
    avg = sum(px) / len(px)
    return sum(1 << i for i, p in enumerate(px) if p >= avg)


def bucket(rgb):
    return tuple(c // 32 for c in rgb[:3])


def opaque_buckets(im):
    small = im.convert("RGBA"); small.thumbnail((128, 128))
    px = small.get_flattened_data() if hasattr(small, "get_flattened_data") else small.getdata()
    return Counter(bucket(p) for p in px if p[3] > 128)


def check_folder(folder, specs):
    names = list_pngs(folder)
    problems, info = {}, {}
    pat = re.compile(specs["name_pattern"])
    seen_sha, hashes, bucket_counts = {}, {}, {}
    for n in names:
        p = os.path.join(folder, n)
        pr = problems.setdefault(n, [])
        if not pat.match(n):
            pr.append("파일명 규칙 위반 (영문 소문자·숫자·하이픈, .png)")
            continue
        try:
            with Image.open(p) as im:
                im.load()
                w, h = im.size
                if w != h:
                    pr.append(f"정사각형이 아님 ({w}x{h})")
                if min(w, h) < specs["min_source_px"]:
                    pr.append(f"너무 작음 ({w}x{h}, 최소 {specs['min_source_px']}px)")
                if not has_alpha(im):
                    pr.append("투명 배경이 아님 (알파 채널 없음)")
                else:
                    a = im.convert("RGBA")
                    corners = [a.getpixel(c)[3] for c in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1))]
                    if max(corners) > specs["corner_alpha_max"]:
                        pr.append("모서리가 투명하지 않음 (배경이 채워져 있음)")
                sha = hashlib.sha256(open(p, "rb").read()).hexdigest()
                if sha in seen_sha:
                    pr.append(f"{seen_sha[sha]} 와 완전히 같은 파일")
                else:
                    seen_sha[sha] = n
                    hashes[n] = ahash(im)
                bucket_counts[n] = opaque_buckets(im)
        except Exception as e:
            pr.append(f"이미지를 열 수 없음: {type(e).__name__}")
    # 비슷한 그림 (같은 모양을 조금 바꾼 것)
    items = sorted(hashes.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            d = bin(items[i][1] ^ items[j][1]).count("1")
            if d <= specs["duplicate_hash_distance"]:
                problems[items[j][0]].append(f"{items[i][0]} 와 매우 비슷함 (해시 거리 {d})")
    # 스타일: 그림 하나를 뺀 나머지 세트의 대표 색(전체의 일정 비율 이상 차지하는 색 칸)에 얼마나 들어가는지
    total = Counter()
    for c in bucket_counts.values():
        total.update(c)
    if len(bucket_counts) >= 3:  # 비교할 나머지가 충분할 때만
        for n, c in bucket_counts.items():
            own = sum(c.values())
            if not own:
                continue
            others = total - c
            osum = sum(others.values())
            if not osum:
                continue
            palette = {b for b, v in others.items() if v / osum >= specs["style_min_share"]}
            cov = sum(v for b, v in c.items() if b in palette) / own
            info[n] = round(cov, 2)
            if cov < specs["style_min_coverage"]:
                problems[n].append(f"나머지 그림들의 대표 색과 많이 다름 (일치 {cov:.0%}) — 스타일이 다를 수 있음")
    ok = [n for n in names if not problems.get(n)]
    bad = {n: p for n, p in problems.items() if p}
    return {"ok": ok, "bad": bad, "total": len(names), "coverage": info}
