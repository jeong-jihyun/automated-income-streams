"""매장 정보 JSON 검사. 글은 여기 적힌 사실만으로 만든다(없는 할인·효능을 지어내지 않음)."""
import json

CATEGORIES = ("cafe", "restaurant", "salon", "shop", "gym", "academy")


class SnsError(ValueError):
    pass


def load(path):
    try:
        s = json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SnsError(f"매장 정보 JSON 오류: {e}")
    for k in ("name", "category", "location", "items"):
        if not s.get(k): raise SnsError(f"매장 정보에 '{k}'가 필요합니다")
    if s["category"] not in CATEGORIES: raise SnsError("category는 " + "/".join(CATEGORIES))
    s.setdefault("tone", "friendly"); s.setdefault("promos", []); s.setdefault("hours", ""); s.setdefault("extra_tags", []); s.setdefault("sponsored", False)
    if s["tone"] not in ("friendly", "formal"): raise SnsError("tone은 friendly/formal")
    return s
