"""시니어 디지털 교육 모임 운영 보조: 수업 배정(정원·대기), 큰 글씨 안내문, 출석 집계. 결제·채팅 없음."""
import csv, re

DAYS = ["월", "화", "수", "목", "금", "토", "일"]


def _read(path, cols):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        miss = [c for c in cols if c not in (r.fieldnames or [])]
        if miss:
            raise ValueError("열이 없습니다: " + ", ".join(miss))
        return list(enumerate(r, start=2))


def mask_phone(p):
    d = re.sub(r"\D", "", p or "")
    return d[:3] + "-****-" + d[-4:] if len(d) >= 10 else "(번호 없음)"


def read_learners(path):
    ok, bad = [], []
    for n, r in _read(path, ["name", "phone", "level", "topics", "weekdays"]):
        try:
            lv = int(r["level"])
            if lv not in (1, 2, 3):
                raise ValueError("level은 1~3")
            wd = {x.strip() for x in r["weekdays"].split(";") if x.strip()}
            if not wd or not wd <= set(DAYS):
                raise ValueError("요일 값 오류")
            if not r["name"].strip():
                raise ValueError("이름 없음")
            ok.append({"name": r["name"].strip(), "phone": r["phone"], "level": lv,
                       "topics": [x.strip() for x in r["topics"].split(";") if x.strip()], "days": wd})
        except ValueError as e:
            bad.append((n, str(e)))
    return ok, bad


def read_classes(path):
    ok, bad = [], []
    for n, r in _read(path, ["id", "topic", "level", "weekday", "time", "capacity"]):
        try:
            lv, cap = int(r["level"]), int(r["capacity"])
            if lv not in (1, 2, 3) or cap < 1 or r["weekday"] not in DAYS or not re.fullmatch(r"\d{2}:\d{2}", r["time"]):
                raise ValueError("수업 값 오류")
            ok.append({"id": r["id"].strip(), "topic": r["topic"].strip(), "level": lv, "day": r["weekday"],
                       "time": r["time"], "cap": cap})
        except ValueError as e:
            bad.append((n, str(e)))
    return ok, bad


def fits(l, c):
    """배울 주제, 요일이 맞고 수업 수준이 본인 수준 이하(편한 수업)이거나 한 단계 위(도전)이면 후보."""
    return c["topic"] in l["topics"] and c["day"] in l["days"] and c["level"] <= l["level"] + 1


def enroll(learners, classes):
    """사람 순서(이름순)대로 후보 중 같은 수준 → 낮은 수준 → 도전 순으로 첫 수업에 넣고 정원이 차면 대기."""
    seats = {c["id"]: [] for c in classes}; wait = {c["id"]: [] for c in classes}; none = []
    for l in sorted(learners, key=lambda x: x["name"]):
        cands = sorted((c for c in classes if fits(l, c)), key=lambda c: (abs(c["level"] - l["level"]) if c["level"] <= l["level"] else 9, c["id"]))
        if not cands:
            none.append(l["name"]); continue
        free = [c for c in cands if len(seats[c["id"]]) < c["cap"]]
        if free:
            seats[free[0]["id"]].append(l["name"])
        else:
            wait[cands[0]["id"]].append(l["name"])
    return seats, wait, none


def notice(c, names, wait=()):
    """큰 글씨용 짧은 안내문(한 줄에 한 가지)."""
    lines = [f"[ {c['topic']} 수업 ]", f"요일: {c['day']}요일", f"시간: {c['time']}", f"수준: {'기초 중급 심화'.split()[c['level'] - 1]}",
             "참석자: " + (", ".join(names) if names else "아직 없음")]
    if wait:
        lines.append("대기: " + ", ".join(wait))
    lines.append("스마트폰을 꼭 가져오세요. 충전도 해 오세요.")
    return "\n".join(lines)


def attendance(path):
    """사람별 출석률과 '연속 2회 결석' 표시(연락 권유). 마지막 기록 기준."""
    rows = [r for _, r in _read(path, ["date", "class_id", "name", "present"])]
    by = {}
    for r in sorted(rows, key=lambda r: (r["name"], r["date"])):
        by.setdefault(r["name"], []).append(r["present"].strip() == "1")
    res = []
    for name, ps in sorted(by.items()):
        streak = 0
        for p in reversed(ps):
            if p: break
            streak += 1
        res.append({"name": name, "rate": round(100 * sum(ps) / len(ps)), "n": len(ps), "reach": streak >= 2})
    return res
