"""주간·월간 회고: 기록 일수, 기분 평균·변화, 자주 나온 낱말, 기분이 높았던/낮았던 날, 대표 문장. 판단·진단은 하지 않는다."""
import datetime
from collections import Counter
from . import summary, text

CRISIS = ("죽고 싶", "죽고싶", "자살", "자해", "사라지고 싶", "살기 싫")
CRISIS_MSG = "기록에 많이 힘든 마음이 담겨 있어요. 혼자 견디지 말고 가까운 사람이나 자살예방상담전화 109(24시간)에 이야기해 보세요. 위급하면 112·119에 연락하세요."
DISCLAIMER = "※ 기록을 정리해 보여 드리는 것일 뿐 마음 상태를 진단하지 않습니다."


def period(data, start, end):
    s, e = datetime.date.fromisoformat(start), datetime.date.fromisoformat(end)
    if e < s: raise ValueError("끝 날짜가 시작보다 빠릅니다")
    return [d for d in data if s <= datetime.date.fromisoformat(d["date"]) <= e], (e - s).days + 1


def crisis(rows):
    return any(c in d["body"] for d in rows for c in CRISIS)


def reflect(data, start, end, llm=None):
    rows, span = period(data, start, end)
    if not rows: return {"empty": True, "text": f"{start}~{end}에는 기록이 없어요.\n{DISCLAIMER}"}
    moods = [d["mood"] for d in rows if d.get("mood")]
    half = len(moods) // 2
    trend = None
    if len(moods) >= 4:
        a, b = sum(moods[:half]) / half, sum(moods[half:]) / (len(moods) - half)
        trend = "올라가는 중" if b - a >= 0.5 else "내려가는 중" if a - b >= 0.5 else "비슷함"
    kw = Counter(w for d in rows for w in text.words(d["body"])).most_common(5)
    best = max((d for d in rows if d.get("mood")), key=lambda d: d["mood"], default=None)
    worst = min((d for d in rows if d.get("mood")), key=lambda d: d["mood"], default=None)
    r = {"empty": False, "days": len(rows), "span": span, "avg_mood": round(sum(moods) / len(moods), 1) if moods else None, "trend": trend,
         "keywords": [w for w, _ in kw], "best": best and best["date"], "worst": worst and worst["date"], "crisis": crisis(rows),
         "highlights": [f"{d['date']}: {' '.join(summary.summarize(d['body'], 1))}" for d in rows[:7]]}
    lines = []
    if r["crisis"]: lines.append(CRISIS_MSG)
    lines.append(f"{start}~{end} 중 {r['days']}일 기록 (기록률 {round(100 * r['days'] / span)}%)")
    if r["avg_mood"]: lines.append(f"기분 평균 {r['avg_mood']}/5" + (f", 흐름: {trend}" if trend else "") + (f" · 높았던 날 {r['best']}, 낮았던 날 {r['worst']}" if r["best"] != r["worst"] else ""))
    if r["keywords"]: lines.append("자주 나온 말: " + ", ".join(r["keywords"]))
    lines += ["- " + h for h in r["highlights"]]
    body = "\n".join(lines)
    if llm and not r["crisis"]:
        try:
            ai = (llm("아래 일기 요약을 따뜻하고 단정하지 않는 3문장 회고로 정리해 줘. 진단·조언 강요 금지.\n" + body) or "").strip()
            if len(ai) >= 20: body += "\n\n[AI 회고] " + ai
        except Exception:
            pass
    r["text"] = body + "\n" + DISCLAIMER
    return r
