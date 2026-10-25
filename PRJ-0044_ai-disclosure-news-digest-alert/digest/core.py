import json, os, re
from difflib import SequenceMatcher
from .rules import classify

DISCLAIMER = "※ 이 알림은 제목만 키워드로 분류한 참고 자료입니다. 매수·매도 권유나 투자 자문이 아니며, 반드시 원문(공시 원문)을 확인하세요."


class DigestError(ValueError):
    pass


def norm(t):
    return re.sub(r"[^0-9a-z가-힣]", "", t.lower())


def similar(a, b, th=0.85):
    return SequenceMatcher(None, norm(a), norm(b)).ratio() >= th


def load_items(path):
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise DigestError(f"항목 파일을 읽지 못했습니다: {e}")
    if not isinstance(data, list): raise DigestError("항목 파일은 목록([...])이어야 합니다")
    for i, it in enumerate(data):
        for k in ("id", "title", "source", "time"):
            if not it.get(k): raise DigestError(f"{i + 1}번째 항목에 '{k}'가 없습니다 (출처·시각 없는 항목은 받지 않습니다)")
    return data


def load_state(path):
    if path and os.path.exists(path):
        try: return set(json.load(open(path, encoding="utf-8")))
        except ValueError: return set()
    return set()


def save_state(path, seen):
    tmp = path + ".tmp"
    json.dump(sorted(seen), open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    os.replace(tmp, path)


def build(items, watch, seen=frozenset(), min_importance=1):
    """watch: 관심 종목명 목록. 반환: (보낼 항목, 건너뜀 통계)."""
    out, skip, kept = [], {"already_sent": 0, "duplicate": 0, "not_watched": 0, "low": 0}, []
    for it in sorted(items, key=lambda x: x["time"]):
        if it["id"] in seen: skip["already_sent"] += 1; continue
        co = next((w for w in watch if w in it["title"] or w == it.get("company")), None)
        if watch and not co: skip["not_watched"] += 1; continue
        cat, imp = classify(it["title"])
        if imp < min_importance: skip["low"] += 1; continue
        dup = next((o for o in kept if o["company"] == co and similar(o["title"], it["title"])), None)
        if dup: dup["also"].append(it["source"]); dup["ids"].append(it["id"]); skip["duplicate"] += 1; continue
        rec = {"id": it["id"], "title": it["title"], "company": co, "category": cat, "importance": imp, "source": it["source"], "time": it["time"], "url": it.get("url", ""), "also": [], "ids": [it["id"]]}
        kept.append(rec)
    out = sorted(kept, key=lambda r: (-r["importance"], r["time"]))
    return out, skip


def render(recs):
    if not recs: return "새로 알릴 항목이 없습니다.\n\n" + DISCLAIMER
    stars = {3: "★★★", 2: "★★", 1: "★"}
    lines = [f"[공시·뉴스 알림] {len(recs)}건"]
    for r in recs:
        also = f" (같은 내용 {len(r['also'])}건 더: {', '.join(r['also'])})" if r["also"] else ""
        lines.append(f"{stars[r['importance']]} [{r['category']}] {r['company'] or '-'} — {r['title']}\n   출처: {r['source']} · {r['time']}{also}" + (f"\n   원문: {r['url']}" if r["url"] else ""))
    return "\n".join(lines) + "\n\n" + DISCLAIMER


def run(items, watch, state_path=None, notifier=print, min_importance=1, dry_run=False):
    """알림을 보낸 뒤에만 '보낸 목록'에 기록한다(보내기 실패하면 다음에 다시 보낸다)."""
    seen = load_state(state_path)
    recs, skip = build(items, watch, seen, min_importance)
    if not recs: return recs, skip, False
    if not dry_run:
        notifier(render(recs))
        if state_path:
            seen |= {i for r in recs for i in r["ids"]}
            save_state(state_path, seen)
    return recs, skip, not dry_run
