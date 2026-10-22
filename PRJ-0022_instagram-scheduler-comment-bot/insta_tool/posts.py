"""예약 게시물 점검과 '지금 올릴 차례' 계산. 인스타그램에 올리는 일은 하지 않는다(발행 함수는 바깥에서 넣음)."""
import csv
import os
import re
from datetime import datetime
from PIL import Image

MAX_CAPTION = 2200      # 알려진 값(정책은 바뀔 수 있어 공식 안내 확인 필요)
MAX_HASHTAGS = 30
RATIO_MIN, RATIO_MAX = 0.8, 1.91   # 세로 4:5 ~ 가로 1.91:1
HASHTAG = re.compile(r"#[\w가-힣]+")


class PostError(ValueError):
    pass


def load(path):
    try:
        rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    except FileNotFoundError:
        raise PostError(f"파일이 없습니다: {path}")
    if not rows or not {"id", "when", "image", "caption"} <= set(rows[0]):
        raise PostError("CSV에 id,when,image,caption 열이 필요합니다")
    return rows


def check(rows, base_dir):
    problems, seen = [], set()
    for i, r in enumerate(rows, 2):
        def bad(m): problems.append((i, m))
        if r["id"] in seen: bad("id가 중복입니다")
        seen.add(r["id"])
        try: datetime.strptime(r["when"], "%Y-%m-%d %H:%M")
        except ValueError: bad("when은 YYYY-MM-DD HH:MM 형식")
        cap = r["caption"] or ""
        if len(cap) > MAX_CAPTION: bad(f"문구가 {MAX_CAPTION}자를 넘습니다 ({len(cap)}자)")
        tags = HASHTAG.findall(cap)
        if len(tags) > MAX_HASHTAGS: bad(f"해시태그가 {MAX_HASHTAGS}개를 넘습니다 ({len(tags)}개)")
        if len(set(t.lower() for t in tags)) != len(tags): bad("같은 해시태그가 반복됩니다")
        p = os.path.join(base_dir, r["image"])
        try:
            w, h = Image.open(p).size
            if not RATIO_MIN <= w / h <= RATIO_MAX: bad(f"사진 비율 {w}:{h}이 허용 범위(4:5 ~ 1.91:1) 밖입니다")
            if min(w, h) < 320: bad("사진이 너무 작습니다 (짧은 변 320px 이상)")
        except (FileNotFoundError, OSError):
            bad(f"사진을 열 수 없습니다: {r['image']}")
    return problems


def due(rows, now, done_ids=()):
    """now 시각까지 올려야 하지만 아직 안 올린 게시물(시간순)."""
    out = []
    for r in rows:
        t = datetime.strptime(r["when"], "%Y-%m-%d %H:%M")
        if t <= now and r["id"] not in done_ids:
            out.append((t, r))
    return [r for _, r in sorted(out, key=lambda x: (x[0], x[1]["id"]))]


def find_conflicts(rows, min_gap_min=60):
    ts = sorted((datetime.strptime(r["when"], "%Y-%m-%d %H:%M"), r["id"]) for r in rows)
    return [(a[1], b[1]) for a, b in zip(ts, ts[1:]) if (b[0] - a[0]).total_seconds() < min_gap_min * 60]
