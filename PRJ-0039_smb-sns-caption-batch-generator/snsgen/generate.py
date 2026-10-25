"""한 달 치 글 만들기: 같은 주제가 연속되지 않고, 같은 글이 반복되지 않게 돌려 쓴다. seed로 재현."""
import datetime
import random
import re
from . import templates as T

def has_batchim(word):
    """마지막 글자에 받침이 있는지(한글만 정확). 영문·숫자로 끝나면 받침 없음으로 본다(간이 처리)."""
    for ch in reversed(word.strip()):
        if "가" <= ch <= "힣": return (ord(ch) - 0xAC00) % 28 != 0
        if ch.isalnum(): return False
    return False


def rieul_batchim(word):
    for ch in reversed(word.strip()):
        if "가" <= ch <= "힣": return (ord(ch) - 0xAC00) % 28 == 8
        if ch.isalnum(): return False
    return False


def fmt(template, **kw):
    """{item|을/를} → 받침 있으면 앞, 없으면 뒤. '으로/로'는 ㄹ받침이면 '로'."""
    def rep(m):
        key, a, b = m.group(1), m.group(2), m.group(3)
        w = kw[key]; use_a = has_batchim(w) and not (a == "으로" and rieul_batchim(w))
        return w + (a if use_a else b)
    return re.sub(r"\{(\w+)\|([^/}]+)/([^}]+)\}", rep, template).format(**kw)


BANNED = re.compile(r"최고|1위|일등|100\s*%|완치|부작용\s*없|무조건|국내\s*유일|기적|특효|세계\s*최초")
MAX_TAGS, MAX_LEN = 10, 2200            # 플랫폼 규정은 바뀔 수 있어 공식 안내로 다시 확인 필요


def tags(s, n=MAX_TAGS):
    base = [s["name"].replace(" ", ""), s["location"].replace(" ", "") + "맛집" if s["category"] in ("cafe", "restaurant") else s["location"].replace(" ", "")]
    seen, out = set(), []
    for t in base + T.TAGS[s["category"]] + s["extra_tags"]:
        t = t.lstrip("#").strip()
        if t and t not in seen: seen.add(t); out.append("#" + t)
    out = out[:n]
    if s["sponsored"] and "#광고" not in out: out = out[:n - 1] + ["#광고"]      # 광고 표시는 자르지 않는다
    return out


def check(caption, s=None):
    probs = []
    if BANNED.search(caption): probs.append("과장·단정 표현: " + BANNED.search(caption).group(0))
    if len(caption) > MAX_LEN: probs.append(f"글이 너무 깁니다({MAX_LEN}자 초과)")
    return probs


def generate(s, start, days, seed=1):
    if not 1 <= days <= 62: raise ValueError("일수는 1~62")
    rng = random.Random(seed); d0 = datetime.date.fromisoformat(start)
    themes = [t for t in T.THEMES if not (t == "이벤트" and not s["promos"]) and not (t == "영업시간 안내" and not s["hours"])]
    last, used, out = None, set(), []
    for i in range(days):
        theme = rng.choice([t for t in themes if t != last]); last = theme
        pool = T.T[theme].get(s["tone"]) or T.T[theme]["friendly"]
        cap = None
        for _ in range(30):                                                    # 이미 쓴 글은 피한다
            item, promo = rng.choice(s["items"]), (rng.choice(s["promos"]) if s["promos"] else "")
            cap = fmt(rng.choice(pool), name=s["name"], item=item, loc=s["location"], hours=s["hours"], promo=promo)
            if cap not in used: break
        repeat = cap in used; used.add(cap)
        out.append({"repeat": repeat, "date": (d0 + datetime.timedelta(days=i)).isoformat(), "theme": theme, "caption": cap, "tags": " ".join(tags(s)), "problems": check(cap, s)})
    return out


def to_csv_rows(posts):
    return [["날짜", "주제", "글", "해시태그", "점검"]] + [[p["date"], p["theme"], p["caption"], p["tags"], "; ".join(p["problems"])] for p in posts]
