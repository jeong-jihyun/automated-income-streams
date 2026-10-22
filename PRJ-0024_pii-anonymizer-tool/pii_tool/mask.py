"""가리는 방법: mask(일부만 *), token([전화] 같은 이름표), hash(같은 값은 같은 가명, 키 필요), redact(완전 삭제 표시)."""
import hashlib
import hmac
import re
from collections import Counter
from . import detect

MODES = ("mask", "token", "hash", "redact")


class MaskError(ValueError):
    pass


def _mask_value(kind, v):
    digits = [i for i, c in enumerate(v) if c.isdigit()]
    if kind in ("rrn",):
        keep = digits[:6]
    elif kind in ("mobile", "phone"):
        keep = digits[:3] + digits[-4:] if len(digits) >= 8 else digits[:2]
    elif kind == "card":
        keep = digits[-4:]
    elif kind == "email":
        local, _, dom = v.partition("@")
        return (local[:1] + "*" * max(len(local) - 1, 1)) + "@" + dom
    elif kind == "name":
        return v[:1] + "*" * (len(v) - 1)
    elif kind == "ip":
        p = v.split("."); return ".".join(p[:2] + ["*", "*"])
    elif kind == "address":
        return v.split()[0] + " ***"
    else:
        keep = digits[-2:]
    return "".join(c if (not c.isdigit() or i in keep) else "*" for i, c in enumerate(v))


def replacement(kind, value, mode, key=None):
    if mode == "mask": return _mask_value(kind, value)
    if mode == "token": return f"[{detect.LABEL[kind]}]"
    if mode == "redact": return "█" * 4
    if mode == "hash":
        if not key: raise MaskError("hash 방식은 --key(비밀 문구)가 필요합니다")
        norm = re.sub(r"[\s.-]", "", value).lower()
        return f"[{detect.LABEL[kind]}:{hmac.new(key.encode(), norm.encode(), hashlib.sha256).hexdigest()[:8]}]"
    raise MaskError(f"mode는 {', '.join(MODES)} 중 하나")


def anonymize(text, mode="token", key=None, kinds=None):
    """(가려진 글, {종류: 개수}) 를 돌려준다. 원본 값은 결과·통계에 남기지 않는다."""
    if mode not in MODES: raise MaskError(f"mode는 {', '.join(MODES)} 중 하나")
    if mode == "hash" and not key: raise MaskError("hash 방식은 --key(비밀 문구)가 필요합니다")
    hits = detect.find(text, kinds)
    out, pos, cnt = [], 0, Counter()
    for s, e, kind, _ in hits:
        out.append(text[pos:s]); out.append(replacement(kind, text[s:e], mode, key)); pos = e; cnt[kind] += 1
    out.append(text[pos:])
    return "".join(out), dict(cnt)
