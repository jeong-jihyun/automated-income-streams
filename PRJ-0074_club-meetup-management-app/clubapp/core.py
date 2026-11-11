"""소모임 회비 현황, 모임 비용 정산(최소 송금 횟수), 일정 공지·참석 집계. 송금·공지 전송은 하지 않는다."""
import csv, datetime as dt
from collections import defaultdict


def _rows(path, need):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        if rd.fieldnames is None or need - set(rd.fieldnames): raise ValueError(f"{path}: 필수 열이 없습니다 - " + ", ".join(sorted(need - set(rd.fieldnames or []))))
        return list(rd)


def read_members(path):
    out = {}
    for i, r in enumerate(_rows(path, {"member", "monthly_due"}), start=2):
        m = r["member"].strip()
        try: due = int(r["monthly_due"])
        except ValueError: raise ValueError(f"{i}행: monthly_due는 정수")
        if not m or m in out or due < 0: raise ValueError(f"{i}행: 회원 id가 비었거나 중복이거나 회비가 음수")
        out[m] = due
    return out


def dues_status(members, payments_path, month, today, due_day=10):
    paid = defaultdict(int)
    for i, r in enumerate(_rows(payments_path, {"member", "month", "amount"}), start=2):
        try: amt = int(r["amount"])
        except ValueError: raise ValueError(f"{i}행: amount는 정수")
        if r["month"].strip() == month: paid[r["member"].strip()] += amt
    deadline = dt.date(int(month[:4]), int(month[5:7]), due_day); res = []
    for m, due in members.items():
        p = paid.get(m, 0)
        st = "완납" if p >= due else ("일부 납부" if p > 0 else "미납")
        if st != "완납" and today > deadline: st += "(기한 지남)"
        res.append({"member": m, "due": due, "paid": p, "left": max(due - p, 0), "over": max(p - due, 0), "status": st})
    unknown = sorted(set(paid) - set(members))
    return res, unknown


def split(amount, people):
    base, rem = divmod(amount, len(people)); return {p: base + (1 if i < rem else 0) for i, p in enumerate(sorted(people))}


def balances(expenses_path):
    bal = defaultdict(int)
    for i, r in enumerate(_rows(expenses_path, {"desc", "payer", "amount", "participants"}), start=2):
        try: amt = int(r["amount"])
        except ValueError: raise ValueError(f"{i}행: amount는 정수")
        ppl = [x.strip() for x in r["participants"].split(";") if x.strip()]
        if amt <= 0 or not ppl: raise ValueError(f"{i}행: 금액은 양수, 참가자는 1명 이상")
        if r["payer"].strip() not in ppl: ppl.append(r["payer"].strip())      # 낸 사람은 참가자에 포함
        for p, share in split(amt, ppl).items(): bal[p] -= share
        bal[r["payer"].strip()] += amt
    return dict(bal)


def transfers(bal):
    """받을 사람(+)과 보낼 사람(-)을 큰 금액부터 맞춰 송금 횟수를 줄인다."""
    cr = sorted([[p, v] for p, v in bal.items() if v > 0], key=lambda x: (-x[1], x[0])); de = sorted([[p, -v] for p, v in bal.items() if v < 0], key=lambda x: (-x[1], x[0]))
    out, i, j = [], 0, 0
    while i < len(cr) and j < len(de):
        amt = min(cr[i][1], de[j][1]); out.append((de[j][0], cr[i][0], amt)); cr[i][1] -= amt; de[j][1] -= amt
        if cr[i][1] == 0: i += 1
        if de[j][1] == 0: j += 1
    return out


def rsvp(path, event):
    c = defaultdict(list)
    for r in _rows(path, {"event", "member", "answer"}):
        if r["event"].strip() == event: c[r["answer"].strip().lower()].append(r["member"].strip())
    return dict(c)


def notice(title, when, place, today, answers=None, members=None):
    d = (when.date() - today).days
    dd = "오늘" if d == 0 else (f"D-{d}" if d > 0 else f"{-d}일 지남")
    L = [f"[모임 공지] {title}", f"일시: {when:%Y-%m-%d %H:%M} ({dd})", f"장소: {place}"]
    if answers is not None:
        L.append(f"참석 {len(answers.get('yes', []))}명 / 불참 {len(answers.get('no', []))}명 / 미정 {len(answers.get('maybe', []))}명")
        if members:
            silent = sorted(set(members) - {x for v in answers.values() for x in v})
            if silent: L.append("아직 답이 없는 사람: " + ", ".join(silent))
    return "\n".join(L)
