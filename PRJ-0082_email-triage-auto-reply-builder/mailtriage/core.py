"""이메일 분류와 답장 초안 만들기. 메일을 보내거나 받아오지 않는다(CSV·JSON 입력만)."""
import csv, io, json, re

SKIP_SENDER = re.compile(r"(^|[^a-z])(no-?reply|do-?not-?reply|mailer-daemon|postmaster)|newsletter", re.I)
SKIP_SUBJECT = re.compile(r"^\s*(auto:|automatic reply|\[광고\]|\(광고\)|자동응답|부재중)", re.I)
URGENT = ("긴급", "오늘까지", "급합니다", "urgent", "asap")
COLS = ["id", "from", "subject", "body"]


def load_rules(path):
    with open(path, encoding="utf-8") as f:
        rules = json.load(f)
    for i, r in enumerate(rules, 1):
        if not r.get("category") or not r.get("keywords") or "reply" not in r:
            raise ValueError(f"규칙 {i}: category, keywords, reply 가 모두 필요합니다")
    return rules


def read_mails(path):
    ok, bad, seen = [], [], set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        miss = [c for c in COLS if c not in (rd.fieldnames or [])]
        if miss:
            raise ValueError("열이 없습니다: " + ", ".join(miss))
        for n, r in enumerate(rd, start=2):
            mid = (r["id"] or "").strip()
            if not mid or mid in seen:
                bad.append((n, "번호가 비었거나 중복")); continue
            if "@" not in (r["from"] or ""):
                bad.append((n, "보낸 사람 주소 오류")); continue
            seen.add(mid); ok.append({"id": mid, "from": r["from"].strip().lower(), "subject": r["subject"] or "", "body": r["body"] or ""})
    return ok, bad


def classify(mail, rules):
    best, score = None, 0
    for r in rules:
        s = sum(2 * mail["subject"].lower().count(k.lower()) + mail["body"].lower().count(k.lower()) for k in r["keywords"])
        if s > score:
            best, score = r, s
    return best


def sender_name(addr):
    return addr.split("@")[0]


def process(mails, rules, replied=()):
    out, done = [], set(replied)
    for m in mails:
        urgent = any(u in (m["subject"] + m["body"]).lower() for u in URGENT)
        rule = classify(m, rules)
        row = {"id": m["id"], "from": m["from"], "category": rule["category"] if rule else "기타",
               "priority": "높음" if urgent else "보통", "draft": "", "note": ""}
        if SKIP_SENDER.search(m["from"]) or SKIP_SUBJECT.search(m["subject"]):
            row["note"] = "자동 발송 메일로 보여 답장 안 함"
        elif m["from"] in done:
            row["note"] = "이미 답장 초안을 만든 상대(중복 방지)"
        elif rule is None:
            row["note"] = "맞는 규칙 없음: 사람이 확인"
        else:
            row["draft"] = rule["reply"].replace("{sender}", sender_name(m["from"])); done.add(m["from"])
        out.append(row)
    return out


def safe(v):
    v = str(v)
    return "'" + v if v[:1] in ("=", "+", "-", "@") else v


def to_csv(rows):
    b = io.StringIO(); w = csv.writer(b, lineterminator="\n"); w.writerow(["id", "from", "category", "priority", "draft", "note"])
    for r in rows:
        w.writerow([safe(r[k]) for k in ("id", "from", "category", "priority", "draft", "note")])
    return b.getvalue()
