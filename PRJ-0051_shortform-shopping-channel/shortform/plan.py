"""제품 정보(JSON)로 세로 숏폼(9:16) 장면표·자막(SRT)·설명 글을 만든다. 광고 표시를 첫 장면과 설명 글에 항상 넣는다."""
import json

DISCLOSURE_SCREEN = "광고 · 구매 시 수수료를 받을 수 있어요"
DISCLOSURE_CAPTION = "#광고 이 영상은 제휴 링크를 포함하며, 구매 시 수수료를 받을 수 있습니다."  # 예시 문구
BAD = ["무조건", "100%", "1위", "최저가", "완치", "기적", "역대급"]
CPS = 6          # 초당 읽을 수 있는 글자 수(여유 있게)
MAX_SECONDS = 60


class PlanError(ValueError):
    pass


def load(path):
    try: return json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e: raise PlanError(f"파일을 읽지 못했습니다: {e}")


def secs(text, minimum=2.0):
    return max(minimum, round(len(text.replace(" ", "")) / CPS, 1))


def make(p):
    miss = [k for k in ("name", "link", "features", "audience") if not p.get(k)]
    if miss: raise PlanError("빠진 항목: " + ", ".join(miss))
    if not (2 <= len(p["features"]) <= 5): raise PlanError("특징은 2~5개로 적어 주세요")
    bad = [w for w in BAD for t in [p["name"]] + p["features"] + [p.get("price_note", "")] if w in t]
    if bad: raise PlanError(f"과장·보장 표현을 빼 주세요: {sorted(set(bad))}")
    scenes = [{"role": "광고 표시+제목", "narration": f"{p['audience']}을 위한 {p['name']}", "screen": [DISCLOSURE_SCREEN, p["name"]]}]
    scenes += [{"role": f"특징 {i}", "narration": f, "screen": [f]} for i, f in enumerate(p["features"], 1)]
    if p.get("price") and p.get("price_date"): scenes.append({"role": "가격", "narration": f"{p['price_date']} 기준 {p['price']:,}원이에요. 바뀔 수 있으니 확인하세요", "screen": [f"{p['price']:,}원 ({p['price_date']} 기준)"]})
    scenes.append({"role": "마무리", "narration": "자세한 내용은 설명란 링크에서 확인하세요", "screen": ["링크는 설명란에"]})
    t = 0.0
    for s in scenes: s["start"] = round(t, 1); s["dur"] = secs(s["narration"]); t += s["dur"]
    total = round(t, 1)
    if total > MAX_SECONDS: raise PlanError(f"영상이 {total}초예요. {MAX_SECONDS}초 이내로 줄여 주세요")
    caption = f"{DISCLOSURE_CAPTION}\n\n{p['name']}\n" + "\n".join(f"- {f}" for f in p["features"]) + f"\n\n구매 링크: {p['link']}\n" + " ".join(p.get("hashtags", []))
    return {"scenes": scenes, "total": total, "caption": caption.strip()}


def srt(plan):
    def ts(x):
        ms = int(round(x * 1000)); return f"{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}"
    return "\n".join(f"{i}\n{ts(s['start'])} --> {ts(s['start'] + s['dur'])}\n{s['narration']}\n" for i, s in enumerate(plan["scenes"], 1))


def check(plan):
    out = []
    if DISCLOSURE_SCREEN not in plan["scenes"][0]["screen"]: out.append("첫 장면에 광고 표시가 없어요")
    if "#광고" not in plan["caption"][:20]: out.append("설명 글 맨 위에 #광고 표시가 없어요")
    if plan["total"] > MAX_SECONDS: out.append("영상이 너무 길어요")
    for s in plan["scenes"]:
        if any(w in s["narration"] for w in BAD): out.append(f"과장 표현: {s['role']}")
    return out
