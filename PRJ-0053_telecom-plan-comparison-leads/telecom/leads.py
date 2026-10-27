"""가입 상담 신청(리드) 기록. 필수 동의가 없으면 저장하지 않는다. 실제로 제휴사에 전송하지 않고 이 컴퓨터의 파일에만 저장한다."""
import json, os, re
from datetime import datetime

PHONE = re.compile(r"^01[016789]-?\d{3,4}-?\d{4}$")
CONSENT_TEXT = {"collect": "개인정보 수집·이용 동의(이름, 연락처 / 상담 연락 목적 / 상담 완료 후 파기) — 필수", "third": "제3자 제공 동의(제공받는 자: 가입 상담 제휴사 / 목적: 가입 상담) — 필수", "marketing": "광고성 정보 수신 동의 — 선택"}  # 예시 문구


class LeadError(ValueError):
    pass


def mask(phone):
    d = re.sub(r"\D", "", phone); return d[:3] + "-****-" + d[-4:]


def validate(name, phone, collect, third, plan_id):
    if not name or not name.strip(): raise LeadError("이름이 필요해요")
    if not PHONE.match(phone or ""): raise LeadError("휴대폰 번호 형식이 올바르지 않아요")
    if not collect: raise LeadError("개인정보 수집·이용 동의가 필요해요(동의 없이는 저장하지 않아요)")
    if not third: raise LeadError("제3자 제공 동의가 필요해요(동의 없이는 저장하지 않아요)")
    if not plan_id: raise LeadError("관심 요금제를 골라 주세요")


def save(path, name, phone, plan_id, collect=False, third=False, marketing=False, now=None):
    validate(name, phone, collect, third, plan_id)
    rec = {"time": (now or datetime.now()).isoformat(timespec="seconds"), "name": name.strip(), "phone": re.sub(r"\D", "", phone), "plan_id": plan_id, "consent": {"collect": True, "third": True, "marketing": bool(marketing)}}
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "a", encoding="utf-8") as f: f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")] if os.path.exists(path) else []


def report(path):
    rs = load(path); lines = [f"상담 신청 {len(rs)}건"]
    for r in rs: lines.append(f"- {r['time']} {r['name'][0]}** {mask(r['phone'])} · {r['plan_id']}" + (" · 광고수신 동의" if r["consent"]["marketing"] else ""))
    return "\n".join(lines)


def delete(path, phone):
    """상담 완료 후 파기: 해당 번호의 기록을 모두 삭제하고 지운 개수를 돌려준다."""
    d = re.sub(r"\D", "", phone); rs = load(path); keep = [r for r in rs if r["phone"] != d]
    with open(path, "w", encoding="utf-8") as f:
        for r in keep: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(rs) - len(keep)
