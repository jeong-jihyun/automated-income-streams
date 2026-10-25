"""반려동물 기록 저장(JSON 파일). 날짜·몸무게·증상·메모·사진(위치정보 제거) 기록."""
import datetime
import json
import os


class PetError(ValueError):
    pass


def load(path):
    if not os.path.exists(path): return {"pets": {}}
    try:
        return json.load(open(path, encoding="utf-8"))
    except json.JSONDecodeError:
        raise PetError(f"기록 파일이 깨졌습니다: {path}")


def save(path, data):
    tmp = path + ".tmp"
    json.dump(data, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, path)                                   # 쓰다 끊겨도 원본이 안 깨지게 교체


def add_pet(data, name, species):
    if species not in ("dog", "cat"): raise PetError("종류는 dog 또는 cat")
    if not name.strip(): raise PetError("이름이 비었습니다")
    if name in data["pets"]: raise PetError("이미 있는 이름입니다")
    data["pets"][name] = {"species": species, "entries": []}


def add_entry(data, name, date, weight_kg=None, symptoms=(), note="", photo=None):
    if name not in data["pets"]: raise PetError(f"없는 반려동물: {name}")
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        raise PetError(f"날짜 형식 오류(YYYY-MM-DD): {date}")
    if weight_kg is not None and not 0.1 <= weight_kg <= 100: raise PetError("몸무게가 비정상입니다(0.1~100kg)")
    data["pets"][name]["entries"].append({"date": date, "weight_kg": weight_kg, "symptoms": [s.strip() for s in symptoms if s.strip()], "note": note.strip(), "photo": photo})
    data["pets"][name]["entries"].sort(key=lambda e: e["date"])
