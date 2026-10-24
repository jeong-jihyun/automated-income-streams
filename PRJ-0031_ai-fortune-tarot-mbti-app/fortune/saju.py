"""간이 사주(연주·일주·시주)와 오행 개수. 월주는 절기 계산이 필요해 구현하지 않음. 연주는 입춘을 2월 4일로 근사."""
import datetime

STEMS, BRANCHES = "갑을병정무기경신임계", "자축인묘진사오미신유술해"
HANJA_S, HANJA_B = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
S_EL = ["목", "목", "화", "화", "토", "토", "금", "금", "수", "수"]
B_EL = ["수", "토", "목", "목", "토", "화", "화", "토", "금", "금", "토", "수"]
REF = datetime.date(1900, 1, 1)          # 갑술일(60갑자 10번)


def _p(i):
    return {"name": STEMS[i % 10] + BRANCHES[i % 12], "hanja": HANJA_S[i % 10] + HANJA_B[i % 12], "stem": i % 10, "branch": i % 12}


def pillars(date, hour=None):
    if date < datetime.date(1900, 1, 1) or date > datetime.date(2100, 12, 31): raise ValueError("1900~2100년만 계산합니다")
    y = date.year - (1 if (date.month, date.day) < (2, 4) else 0)
    out = {"year": _p((y - 4) % 60), "day": _p((10 + (date - REF).days) % 60)}
    if hour is not None:
        if not 0 <= hour <= 23: raise ValueError("시간은 0~23")
        b = ((hour + 1) // 2) % 12
        stem = (out["day"]["stem"] % 5 * 2 + b) % 10
        out["hour"] = {"name": STEMS[stem] + BRANCHES[b], "hanja": HANJA_S[stem] + HANJA_B[b], "stem": stem, "branch": b}
    return out


def elements(p):
    cnt = {"목": 0, "화": 0, "토": 0, "금": 0, "수": 0}
    for v in p.values():
        cnt[S_EL[v["stem"]]] += 1; cnt[B_EL[v["branch"]]] += 1
    return cnt
