"""방문 메모(JSON)로 맛집·카페 후기 초안과 지역별 목차를 만든다. 방문한 날짜·직접 느낀 점이 없으면 만들지 않는다."""
import json
from datetime import date

SPONSOR_NOTE = "※ 이 글은 업체로부터 {what}을(를) 제공받아 작성했습니다. 내용은 직접 경험한 대로 솔직하게 썼습니다."  # 예시 문구, 최신 공식 표기 방식은 직접 확인
BAD = ["인생맛집", "무조건", "100%", "최고의", "역대급", "미친", "안 가면 후회"]
MIN_PHOTOS = 5


class ReviewError(ValueError):
    pass


def load(path):
    try: return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise ReviewError(f"파일을 읽지 못했습니다: {e}")


def validate(v, today):
    miss = [k for k in ("place", "region", "category", "visited", "address") if not v.get(k)]
    if miss: raise ReviewError("빠진 항목: " + ", ".join(miss))
    try: d = date.fromisoformat(v["visited"])
    except ValueError: raise ReviewError("방문일은 YYYY-MM-DD 형식이어야 해요")
    if d > today: raise ReviewError("방문일이 미래예요. 가 보지 않은 곳의 후기는 만들지 않아요")
    if not v.get("menu"): raise ReviewError("먹어 본 메뉴(menu)를 1개 이상 적어 주세요")
    for m in v["menu"]:
        if not m.get("name") or not m.get("comment"): raise ReviewError("메뉴마다 이름(name)과 직접 느낀 점(comment)이 필요해요")
    if v.get("sponsored") and not v.get("sponsor_provided"): raise ReviewError("협찬이면 무엇을 받았는지(sponsor_provided)를 적어 주세요")
    return d


def make(v, today=None):
    today = today or date.today(); validate(v, today); li = lambda xs: "\n".join(f"- {x}" for x in xs)
    menu = "\n".join(f"- {m['name']}" + (f" {m['price']:,}원" if m.get("price") else "") + f": {m['comment']}" for m in v["menu"])
    sp = (SPONSOR_NOTE.format(what=v["sponsor_provided"]) + "\n\n") if v.get("sponsored") else ""
    cons = f"\n## 아쉬웠던 점\n{li(v['cons'])}\n" if v.get("cons") else ""
    tags = " ".join(f"#{t.replace(' ', '')}" for t in [v["region"] + v["category"], v["region"] + "맛집" if v["category"] != "카페" else v["region"] + "카페", v["place"]])
    return (f"{sp}# {v['region']} {v['place']} 방문 후기 ({v['visited']} 방문)\n\n## 기본 정보\n- 주소: {v['address']}\n" + (f"- 영업시간: {v['hours']} (방문 시점 기준, 바뀔 수 있어요)\n" if v.get("hours") else "")
            + f"\n## 먹어 본 메뉴 (가격은 {v['visited']} 기준)\n{menu}\n" + (f"\n## 좋았던 점\n{li(v['pros'])}\n" if v.get("pros") else "") + cons
            + f"\n[직접 찍은 사진 {MIN_PHOTOS}장 이상을 넣어 주세요]\n\n{tags}\n" + ("\n" + sp.strip() + "\n" if sp else ""))


def check(text, photos=0, sponsored=False):
    out = []
    if sponsored and "제공받아" not in text[:200]: out.append(("협찬", "협찬 글인데 맨 위에 협찬 표시가 없어요"))
    if sponsored and "제공받아" not in text[-300:]: out.append(("협찬", "글 맨 아래에도 협찬 표시를 넣으면 좋아요"))
    for w in BAD:
        if w in text: out.append(("과장", f"'{w}' 표현은 빼 주세요"))
    if photos < MIN_PHOTOS: out.append(("사진", f"직접 찍은 사진이 {MIN_PHOTOS}장 이상 필요해요(현재 {photos}장)"))
    if "방문" not in text or "기준" not in text: out.append(("날짜", "방문일과 '기준' 표기가 없어요(가격·영업시간은 바뀔 수 있어요)"))
    return out


def index(visits):
    by = {}
    for v in visits: by.setdefault(v["region"], []).append(v)
    lines = ["# 지역별 후기 목차"]
    for r in sorted(by):
        lines.append(f"\n## {r}")
        for v in sorted(by[r], key=lambda x: x["visited"], reverse=True): lines.append(f"- {v['place']} ({v['category']}, {v['visited']} 방문)" + (" · 협찬" if v.get("sponsored") else ""))
    return "\n".join(lines) + "\n"
