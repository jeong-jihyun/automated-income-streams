"""반려동물 돌봄 매칭 (결제·연락·후기 기능 없음). 요청 CSV와 돌봄이 CSV를 받아 조건이 맞는 짝을 정한다."""
import csv, datetime as dt
from collections import Counter

SIZES = {"small": 1, "medium": 2, "large": 3}
REQ_COLS = ["id", "owner", "region", "pet", "size", "start", "end"]
SIT_COLS = ["name", "regions", "pets", "max_size", "capacity", "avail_from", "avail_to"]


def _rows(path, cols):
    with open(path, encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        miss = [c for c in cols if c not in (r.fieldnames or [])]
        if miss:
            raise ValueError("열이 없습니다: " + ", ".join(miss))
        return list(enumerate(r, start=2))


def read_requests(path):
    ok, bad, seen = [], [], set()
    for n, r in _rows(path, REQ_COLS):
        try:
            s, e = dt.date.fromisoformat(r["start"].strip()), dt.date.fromisoformat(r["end"].strip())
            if e < s:
                raise ValueError("끝 날짜가 시작보다 빠름")
            size = r["size"].strip().lower()
            if size not in SIZES:
                raise ValueError("크기 값 오류")
            rid = r["id"].strip()
            if not rid or rid in seen:
                raise ValueError("번호가 비었거나 중복")
            seen.add(rid)
            ok.append({"id": rid, "owner": r["owner"].strip(), "region": r["region"].strip(),
                       "pet": r["pet"].strip().lower(), "size": size, "start": s, "end": e})
        except ValueError as ex:
            bad.append((n, str(ex)))
    return ok, bad


def read_sitters(path):
    ok, bad = [], []
    for n, r in _rows(path, SIT_COLS):
        try:
            ms = r["max_size"].strip().lower()
            if ms not in SIZES:
                raise ValueError("max_size 값 오류")
            cap = int(r["capacity"])
            if cap < 1:
                raise ValueError("capacity는 1 이상")
            a, b = dt.date.fromisoformat(r["avail_from"].strip()), dt.date.fromisoformat(r["avail_to"].strip())
            if b < a:
                raise ValueError("가능 기간 오류")
            ok.append({"name": r["name"].strip(), "regions": {x.strip() for x in r["regions"].split(";") if x.strip()},
                       "pets": {x.strip().lower() for x in r["pets"].split(";") if x.strip()},
                       "max_size": ms, "capacity": cap, "from": a, "to": b})
        except ValueError as ex:
            bad.append((n, str(ex)))
    return ok, bad


def overlap(a, b):
    return a["start"] <= b["end"] and b["start"] <= a["end"]


def why_not(req, sit, assigned):
    """맞지 않는 이유 한 가지(맞으면 None)."""
    if req["region"] not in sit["regions"]:
        return "지역 불일치"
    if req["pet"] not in sit["pets"]:
        return "동물 종류 불가"
    if SIZES[req["size"]] > SIZES[sit["max_size"]]:
        return "크기 초과"
    if req["start"] < sit["from"] or req["end"] > sit["to"]:
        return "가능 기간 밖"
    if sum(1 for x in assigned if overlap(x, req)) >= sit["capacity"]:
        return "동시 돌봄 정원 초과"
    return None


def match(reqs, sitters):
    """빨리 시작하는 요청부터, 후보가 적은 요청 우선. 후보 중 현재 배정이 적은 사람, 같으면 이름순."""
    book = {s["name"]: [] for s in sitters}
    done, left = [], []
    order = sorted(reqs, key=lambda r: (r["start"], sum(1 for s in sitters if not why_not(r, s, [])), r["id"]))
    for r in order:
        cands = [s for s in sitters if not why_not(r, s, book[s["name"]])]
        if not cands:
            c = Counter(why_not(r, s, book[s["name"]]) for s in sitters)
            left.append((r, c.most_common(1)[0][0] if c else "돌봄이 없음"))
            continue
        pick = min(cands, key=lambda s: (len(book[s["name"]]), s["name"]))
        book[pick["name"]].append(r)
        done.append((r, pick["name"]))
    return sorted(done, key=lambda x: x[0]["id"]), sorted(left, key=lambda x: x[0]["id"])


def report(done, left, bad_req, bad_sit):
    out = [f"배정 {len(done)}건 / 미배정 {len(left)}건"]
    out += [f"- {r['id']} {r['pet']}({r['size']}) {r['start']}~{r['end']} → {n}" for r, n in done]
    if left:
        out.append("미배정:")
        out += [f"- {r['id']}: {why}" for r, why in left]
    for label, bad in (("요청", bad_req), ("돌봄이", bad_sit)):
        for n, why in bad:
            out.append(f"[제외] {label} {n}행: {why}")
    out.append("※ 연락·결제·후기는 이 도구가 하지 않습니다. 배정은 후보 추천이며 당사자 확인이 필요합니다.")
    return "\n".join(out)
