"""일반 건강 정보 안내(진단·약 용량 안내 없음). 응급 신호는 바로 병원 안내, 추세는 기록 기준으로만 알려 준다."""
import datetime

URGENT = {  # 증상 표현 → 안내. 흔히 알려진 응급 신호만 담은 보수적 목록(수의사 검토를 받은 것이 아님)
    "호흡곤란": "숨쉬기 힘든 모습은 응급일 수 있습니다.", "경련": "경련은 응급일 수 있습니다.", "발작": "발작은 응급일 수 있습니다.",
    "초콜릿": "초콜릿 섭취는 위험할 수 있습니다.", "자일리톨": "자일리톨 섭취는 위험할 수 있습니다.", "포도": "포도·건포도 섭취는 위험할 수 있습니다.",
    "피 섞인 구토": "피가 섞인 구토는 응급일 수 있습니다.", "혈변": "혈변은 빨리 진료가 필요할 수 있습니다.",
    "소변 못": "소변을 못 보는 것은 특히 고양이에서 응급일 수 있습니다.", "배가 부풀": "갑자기 배가 부푸는 것은 응급일 수 있습니다.",
    "의식": "의식이 흐린 것은 응급일 수 있습니다.", "쓰러": "쓰러짐은 응급일 수 있습니다.", "독": "독성 물질 섭취가 의심되면 응급입니다.",
}
WATCH = {"구토": 3, "설사": 3, "기침": 5, "식욕부진": 3, "절뚝": 3}      # 최근 7일 안에 이 횟수 이상이면 진료 상담 권장
DISCLAIMER = "※ 일반 정보이며 진단이 아닙니다. 약 이름·용량은 안내하지 않습니다. 걱정되면 수의사와 상담하세요."


def urgent_signs(entry_symptoms, note=""):
    text = " ".join(entry_symptoms) + " " + note
    return [msg for key, msg in URGENT.items() if key in text]


def weight_trend(entries, days=30, limit=0.10):
    pts = [(datetime.date.fromisoformat(e["date"]), e["weight_kg"]) for e in entries if e.get("weight_kg")]
    if len(pts) < 2: return None
    last_d, last_w = pts[-1]
    base = [p for p in pts if (last_d - p[0]).days <= days and p[0] != last_d]
    if not base: return None
    first_d, first_w = base[0]
    ch = (last_w - first_w) / first_w
    return {"from": first_w, "to": last_w, "change_pct": round(ch * 100, 1), "flag": abs(ch) >= limit}


def repeated(entries, today, window=7):
    t = datetime.date.fromisoformat(today); cnt = {}
    for e in entries:
        if 0 <= (t - datetime.date.fromisoformat(e["date"])).days < window:
            for s in e["symptoms"]:
                for k in WATCH:
                    if k in s: cnt[k] = cnt.get(k, 0) + 1
    return {k: n for k, n in cnt.items() if n >= WATCH[k]}


def advise(pet, today):
    out = {"urgent": [], "watch": [], "weight": None, "text": ""}
    recent = [e for e in pet["entries"] if 0 <= (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(e["date"])).days <= 1]
    for e in recent: out["urgent"] += urgent_signs(e["symptoms"], e["note"])
    out["urgent"] = sorted(set(out["urgent"]))
    out["watch"] = [f"최근 7일 '{k}' 기록 {n}회" for k, n in repeated(pet["entries"], today).items()]
    out["weight"] = weight_trend(pet["entries"])
    lines = []
    if out["urgent"]: lines.append("🚨 지금 동물병원(또는 24시 응급병원)에 연락하세요. " + " ".join(out["urgent"]))
    lines += [f"⚠ {w} — 진료 상담을 권합니다." for w in out["watch"]]
    w = out["weight"]
    if w and w["flag"]: lines.append(f"⚠ 몸무게가 {w['from']}kg → {w['to']}kg ({w['change_pct']:+}%)로 변했습니다. 수의사와 상담해 보세요.")
    if not lines: lines.append("기록상 눈에 띄는 위험 신호는 없습니다. 계속 기록해 주세요.")
    out["text"] = "\n".join(lines) + "\n" + DISCLAIMER
    return out
