"""문자·알림톡 발송 준비: 문구 채우기, 번호·수신동의·야간 점검, SMS/LMS 판정, outbox 파일 만들기. 실제로 보내지 않는다."""
import csv, json, re

AD_PREFIX, AD_SUFFIX = "(광고) ", "\n무료수신거부 080-000-0000"  # 번호는 예시이며 실제 번호로 바꿔야 한다
SMS_MAX, LMS_MAX = 90, 2000
VAR = re.compile(r"\{(\w+)\}")


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    if d.startswith("82") and len(d) in (11, 12):
        d = "0" + d[2:]
    return d if re.fullmatch(r"01[016789]\d{7,8}", d) else None


def load_templates(path):
    t = json.load(open(path, encoding="utf-8"))
    for k, v in t.items():
        if not isinstance(v, dict) or not v.get("text") or v.get("kind") not in ("info", "ad"):
            raise ValueError(f"템플릿 {k}: text 와 kind(info 또는 ad)가 필요합니다")
    return t


def is_quiet(hhmm):
    """광고 문자 금지 시간(21:00~다음날 08:00, 예시 설정)."""
    h, m = map(int, hhmm.split(":"))
    if not (0 <= h < 24 and 0 <= m < 60):
        raise ValueError("시간 형식 오류(HH:MM)")
    return h >= 21 or h < 8


def size_kind(text):
    try:
        n = len(text.encode("cp949"))
    except UnicodeEncodeError:
        return None, "표현할 수 없는 글자(이모지 등)"
    if n <= SMS_MAX:
        return "SMS", None
    return ("LMS", None) if n <= LMS_MAX else (None, "2000바이트 초과")


def build(tpl, recipients, send_at):
    out, skipped, seen = [], [], set()
    quiet = is_quiet(send_at)
    for n, r in enumerate(recipients, start=2):
        phone = norm_phone(r.get("phone"))
        if not phone:
            skipped.append((n, "휴대폰 번호 형식 오류")); continue
        missing = [v for v in VAR.findall(tpl["text"]) if not (r.get(v) or "").strip()]
        if missing:
            skipped.append((n, "채울 값 없음: " + ",".join(missing))); continue
        if tpl["kind"] == "ad":
            if r.get("consent_ad", "").strip() != "1":
                skipped.append((n, "광고 수신 동의 없음")); continue
            if quiet:
                skipped.append((n, f"광고 금지 시간대({send_at})")); continue
        text = VAR.sub(lambda m: r[m.group(1)].strip(), tpl["text"])
        if tpl["kind"] == "ad":
            text = AD_PREFIX + text + AD_SUFFIX
        kind, why = size_kind(text)
        if why:
            skipped.append((n, why)); continue
        if (phone, text) in seen:
            skipped.append((n, "같은 번호에 같은 문구 중복")); continue
        seen.add((phone, text)); out.append({"to": phone, "type": kind, "text": text, "send_at": send_at, "status": "READY"})
    return out, skipped


def read_recipients(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        if "phone" not in (rd.fieldnames or []):
            raise ValueError("phone 열이 없습니다")
        return list(rd)
