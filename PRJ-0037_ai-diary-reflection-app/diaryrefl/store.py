import datetime
import json
import os


class DiaryError(ValueError):
    pass


def load(path):
    if not os.path.exists(path): return []
    try:
        return json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        raise DiaryError(f"일기 파일이 깨졌습니다: {path}")


def save(path, data):
    tmp = path + ".tmp"; json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1); os.replace(tmp, path)


def add(data, date, body, mood=None):
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise DiaryError(f"날짜 형식 오류(YYYY-MM-DD): {date}")
    if not body.strip(): raise DiaryError("내용이 비었습니다")
    if mood is not None and mood not in (1, 2, 3, 4, 5): raise DiaryError("기분은 1~5")
    for e in data:
        if e["date"] == date: e["body"] = e["body"] + "\n" + body.strip(); e["mood"] = mood if mood is not None else e.get("mood"); return data   # 같은 날은 이어 붙임
    data.append({"date": date, "body": body.strip(), "mood": mood}); data.sort(key=lambda e: e["date"]); return data
