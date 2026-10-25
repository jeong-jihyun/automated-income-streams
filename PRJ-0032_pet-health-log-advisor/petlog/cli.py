import argparse
import datetime
from . import advice, report, store


def main(argv=None):
    p = argparse.ArgumentParser(prog="petlog", description="반려동물 건강 기록 + 일반 정보 안내 (진단 아님)")
    p.add_argument("--file", default="pets.json")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("add-pet"); s.add_argument("name"); s.add_argument("species", choices=["dog", "cat"])
    s = sub.add_parser("log"); s.add_argument("name"); s.add_argument("--date"); s.add_argument("--weight", type=float); s.add_argument("--symptom", action="append", default=[]); s.add_argument("--note", default="")
    s = sub.add_parser("advise"); s.add_argument("name"); s.add_argument("--today")
    s = sub.add_parser("report"); s.add_argument("name"); s.add_argument("--today"); s.add_argument("--out")
    a = p.parse_args(argv)
    today = getattr(a, "today", None) or getattr(a, "date", None) or datetime.date.today().isoformat()
    try:
        d = store.load(a.file)
        if a.cmd == "add-pet": store.add_pet(d, a.name, a.species); store.save(a.file, d); print("[완료] 등록")
        elif a.cmd == "log":
            store.add_entry(d, a.name, a.date or today, a.weight, a.symptom, a.note); store.save(a.file, d)
            u = advice.urgent_signs(a.symptom, a.note); print("[완료] 기록 저장")
            if u: print("🚨 응급 신호가 있습니다. 바로 동물병원에 연락하세요. " + " ".join(u))
        elif a.cmd == "advise":
            if a.name not in d["pets"]: raise store.PetError(f"없는 반려동물: {a.name}")
            print(advice.advise(d["pets"][a.name], today)["text"])
        else:
            if a.name not in d["pets"]: raise store.PetError(f"없는 반려동물: {a.name}")
            md = report.vet_summary(a.name, d["pets"][a.name], today)
            open(a.out, "w", encoding="utf-8").write(md) if a.out else print(md)
        return 0
    except store.PetError as e:
        print(f"[오류] {e}"); return 2
