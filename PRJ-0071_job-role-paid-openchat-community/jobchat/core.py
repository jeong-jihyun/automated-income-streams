"""직무별 유료 모임 운영 보조: 회원 기간 점검, 모의 면접 짝짓기, 게시글 규칙 점검. 오픈채팅·결제 연동 없음."""
import csv, datetime as dt, re

LEVELS = {"주니어": 1, "미들": 2, "시니어": 3}
SOON = 7
RULES = [("연락처 공개", re.compile(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}|카톡\s*id|카카오\s*id|오픈채팅\s*링크|텔레그램\s*@", re.I)),
         ("외부 결제·입금 유도", re.compile(r"입금|계좌\s*번호|송금|선결제")),
         ("수익·합격 보장 표현", re.compile(r"100\s*%\s*합격|합격\s*보장|수익\s*보장|무조건\s*(합격|성공)")),
         ("홍보·광고", re.compile(r"(광고|홍보)\s*(문의|환영)|할인\s*코드|추천인\s*코드"))]


def read_members(path):
    out, seen = [], set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        need = {"member_id", "role", "level", "paid_until", "slots"}
        if rd.fieldnames is None or need - set(rd.fieldnames): raise ValueError("필수 열이 없습니다: " + ", ".join(sorted(need - set(rd.fieldnames or []))))
        for i, r in enumerate(rd, start=2):
            mid = r["member_id"].strip()
            if not mid or mid in seen: raise ValueError(f"{i}행: 회원 id가 비었거나 중복입니다")
            seen.add(mid)
            if r["level"].strip() not in LEVELS: raise ValueError(f"{i}행: level은 {'/'.join(LEVELS)} 중 하나")
            try: pu = dt.date.fromisoformat(r["paid_until"].strip())
            except ValueError: raise ValueError(f"{i}행: paid_until 날짜 형식 오류")
            out.append({"id": mid, "role": r["role"].strip(), "level": r["level"].strip(), "paid_until": pu,
                        "slots": {s.strip() for s in r["slots"].split(";") if s.strip()}, "want": (r.get("want") or "").strip()})
    return out


def status(m, today):
    d = (m["paid_until"] - today).days
    return "만료" if d < 0 else ("곧 만료" if d <= SOON else "이용 중")


def reminders(members, today):
    out = []
    for m in members:
        s = status(m, today); d = (m["paid_until"] - today).days
        if s == "곧 만료": out.append((m["id"], f"{m['id']}님, 이용 기간이 {d}일 뒤({m['paid_until']})에 끝납니다. 계속 이용하시려면 연장 안내를 확인해 주세요."))
        elif s == "만료": out.append((m["id"], f"{m['id']}님, 이용 기간이 {m['paid_until']}에 끝났습니다. 모의 면접 매칭에서는 제외됩니다."))
    return out


def match(members, today):
    """같은 직무·겹치는 시간대·이용 중인 회원끼리 짝짓기. 레벨이 높은 사람이 면접관. 한 사람은 한 번만."""
    act = [m for m in members if status(m, today) != "만료"]
    used, pairs = set(), []
    for role in sorted({m["role"] for m in act}):
        pool = sorted([m for m in act if m["role"] == role], key=lambda m: (-LEVELS[m["level"]], m["id"]))
        for a in pool:
            if a["id"] in used: continue
            for b in sorted(pool, key=lambda m: (LEVELS[m["level"]], m["id"])):
                if b["id"] == a["id"] or b["id"] in used: continue
                common = sorted(a["slots"] & b["slots"])
                if common:
                    ia, ca = (a, b) if LEVELS[a["level"]] >= LEVELS[b["level"]] else (b, a)
                    pairs.append({"role": role, "interviewer": ia["id"], "candidate": ca["id"], "slot": common[0]}); used.update({a["id"], b["id"]}); break
    left = []
    for m in members:
        if m["id"] in used: continue
        why = "이용 기간 만료" if status(m, today) == "만료" else ("같은 직무에 다른 회원이 없음" if sum(1 for x in act if x["role"] == m["role"]) < 2 else "겹치는 시간대가 있는 상대가 없음")
        left.append((m["id"], why))
    return pairs, left


def check_post(text):
    return [name for name, rx in RULES if rx.search(text)]


def report(members, today):
    pairs, left = match(members, today); L = [f"기준일 {today}"]
    for s in ("이용 중", "곧 만료", "만료"): L.append(f"- {s}: {sum(1 for m in members if status(m, today) == s)}명")
    L.append("모의 면접 짝:")
    L += [f"  [{p['role']}] 면접관 {p['interviewer']} ↔ 지원자 {p['candidate']} ({p['slot']})" for p in pairs] or ["  (없음)"]
    L += [f"  짝 없음: {i} - {w}" for i, w in left]
    L.append("※ 안내 문구는 초안이며 보내지 않습니다. 오픈채팅·디스코드·결제는 연동하지 않았습니다.")
    return "\n".join(L)
