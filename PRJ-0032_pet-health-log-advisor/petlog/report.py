"""병원에 가져갈 요약(최근 기록 표)."""
import datetime


def vet_summary(name, pet, today, days=30):
    t = datetime.date.fromisoformat(today)
    rows = [e for e in pet["entries"] if 0 <= (t - datetime.date.fromisoformat(e["date"])).days <= days]
    out = [f"# {name} ({'강아지' if pet['species'] == 'dog' else '고양이'}) 최근 {days}일 기록", "", "| 날짜 | 몸무게(kg) | 증상 | 메모 |", "|---|---|---|---|"]
    for e in rows: out.append(f"| {e['date']} | {e['weight_kg'] or ''} | {', '.join(e['symptoms'])} | {e['note'].replace('|', '/')} |")
    if not rows: out.append("| (기록 없음) | | | |")
    return "\n".join(out) + "\n"
