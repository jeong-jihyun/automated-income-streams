"""하루 식사 기록. 목표 칼로리·감량 조언은 일부러 넣지 않았다(섭식 문제 위험)."""
import json
import os


def add(path, date, meal, res):
    d = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    d.setdefault(date, []).append({"meal": meal, "kcal": res["kcal"], "low": res["low"], "high": res["high"], "foods": [r["label"] for r in res["rows"]]})
    tmp = path + ".tmp"; json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, path)


def day(path, date):
    d = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    m = d.get(date, [])
    return {"meals": m, "kcal": sum(x["kcal"] for x in m), "low": sum(x["low"] for x in m), "high": sum(x["high"] for x in m)}
